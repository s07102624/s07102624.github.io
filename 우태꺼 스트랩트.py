import time
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')  # 새로운 헤드리스 모드
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    driver = webdriver.Chrome(
        options=chrome_options
    )
    return driver

def clean_filename(text):
    return re.sub(r'[\\/*?:"<>|]', "", text)

def scrape_article(driver, url):
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'entry-content'))
        )
        
        # 원본 HTML 전체 구조 가져오기
        title = driver.find_element(By.CSS_SELECTOR, 'h1.entry-title').get_attribute('outerHTML')
        content = driver.find_element(By.CLASS_NAME, 'entry-content').get_attribute('outerHTML')
        head_content = driver.find_element(By.TAG_NAME, 'head').get_attribute('innerHTML')
        
        # 네비게이션 메뉴 가져오기
        nav_menu = ''
        try:
            nav_menu = driver.find_element(By.CLASS_NAME, 'main-navigation').get_attribute('outerHTML')
        except:
            pass
        
        return title, content, head_content, nav_menu
    except Exception as e:
        print(f'Error scraping article {url}: {str(e)}')
        return None, None, None, None

def create_html_content(url, title, content, head_content, nav_menu):
    html_template = f'''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    {head_content}
</head>
<body>
    <div id="page" class="site">
        {nav_menu}
        <div id="content" class="site-content">
            <div id="primary" class="content-area">
                <main id="main" class="site-main">
                    <article class="post">
                        {title}
                        {content}
                    </article>
                </main>
            </div>
        </div>
    </div>
</body>
</html>'''
    return html_template

def scrape_category():
    driver = setup_driver()
    base_url = 'https://insurance.friendwoo.com/'
    page = 1
    max_pages = 100
    
    import os
    news_dir = 'news'
    if not os.path.exists(news_dir):
        os.makedirs(news_dir)
    
    try:
        while page <= max_pages:
            url = f'{base_url}page/{page}'
            print(f"\n=== Scraping page {page}: {url} ===")
            driver.get(url)
            time.sleep(3)
            
            try:
                # 게시물 목록 찾기
                articles = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'article.post'))
                )
                
                if not articles:
                    print("게시물을 찾을 수 없습니다.")
                    break
                
                print(f"Found {len(articles)} articles on page {page}")
                
                # 현재 페이지의 모든 게시물 처리
                for article in articles:
                    try:
                        # 게시물 링크 찾기
                        link = article.find_element(By.CSS_SELECTOR, 'h2.entry-title a').get_attribute('href')
                        print(f"\nProcessing article: {link}")
                        
                        # 상세 페이지로 이동
                        driver.get(link)
                        time.sleep(2)
                        
                        # 상세 페이지 처리 부분 수정
                        title, content, head_content, nav_menu = scrape_article(driver, link)
                        
                        if title and content:
                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                            safe_title = clean_filename(title)[:50]
                            filename = os.path.join(news_dir, f'scrape_{safe_title}_{timestamp}.html')
                            
                            html_content = create_html_content(link, title, content, head_content, nav_menu)
                            
                            with open(filename, 'w', encoding='utf-8') as f:
                                f.write(html_content)
                            
                            print(f'Successfully saved HTML: {filename}')
                            
                    except Exception as e:
                        print(f'게시물 처리 오류: {str(e)}')
                        continue
                
                # 다음 페이지로
                page += 1
                time.sleep(2)
                
            except Exception as e:
                print(f"페이지 처리 오류: {str(e)}")
                break
    
    except Exception as e:
        print(f'스크래핑 오류: {str(e)}')
    finally:
        driver.quit()

if __name__ == '__main__':
    print('Starting to scrape insurance.friendwoo.com category...')
    scrape_category()
    print('Scraping completed!')
