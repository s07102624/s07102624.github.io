import time
import re
import sys
import random
import logging
import os
from datetime import datetime
try:
    from bs4 import BeautifulSoup
    import cloudscraper
    from fake_useragent import UserAgent
except ImportError as e:
    print(f"필요한 패키지가 설치되지 않았습니다: {str(e)}")
    print("다음 명령어로 필요한 패키지를 설치하세요:")
    print("pip install beautifulsoup4 cloudscraper fake-useragent")
    sys.exit(1)

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def clean_filename(text):
    return re.sub(r'[\\/*?:"<>|]', "", text)

def get_scraper():
    """클라우드플레어 우회 스크래퍼 생성"""
    ua = UserAgent()
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    scraper.headers.update({
        'User-Agent': ua.random,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://www.humorworld.net/',
        'DNT': '1',
    })
    return scraper

def setup_folders():
    """필요한 폴더 구조 생성"""
    base_path = os.path.join('s07102624.github.io', 'output', 'news')
    image_path = os.path.join(base_path, 'images')
    
    # 폴더 생성
    os.makedirs(base_path, exist_ok=True)
    os.makedirs(image_path, exist_ok=True)
    
    return base_path, image_path

def save_article(title, content, images, base_path):
    """HTML 파일로 게시물 저장"""
    safe_title = clean_filename(title)
    filename = os.path.join(base_path, f'{safe_title}.html')
    
    html_content = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; }}
        img {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <div class="content">
        {content}
    </div>
    <div class="images">
        {images}
    </div>
</body>
</html>
"""
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return filename

def scrape_category():
    base_path, image_path = setup_folders()
    try:
        scraper = get_scraper()
    except Exception as e:
        logging.error(f"스크래퍼 초기화 실패: {str(e)}")
        return

    base_url = 'https://humorworld.net/category/humorstorage/'
    page = 1
    
    try:
        while True:
            url = f'{base_url}page/{page}/' if page > 1 else base_url
            logging.info(f"Scraping page {page}: {url}")
            
            response = scraper.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            articles = soup.select('article.format-standard')
            if not articles:
                break
                
            for article in articles:
                try:
                    title_elem = article.select_one('.entry-title a')
                    if not title_elem:
                        continue
                    
                    link = title_elem.get('href')
                    title = title_elem.get_text(strip=True)
                    
                    # 게시물 내용 스크래핑
                    article_response = scraper.get(link)
                    article_soup = BeautifulSoup(article_response.text, 'html.parser')
                    content = article_soup.select_one('.entry-content')
                    
                    if content:
                        # 이미지 처리
                        images_html = ""
                        for img in content.find_all('img'):
                            if img.get('src'):
                                img_name = f"{clean_filename(img['src'].split('/')[-1])}"
                                img_path = os.path.join(image_path, img_name)
                                
                                # 이미지 다운로드
                                try:
                                    img_response = scraper.get(img['src'])
                                    with open(img_path, 'wb') as f:
                                        f.write(img_response.content)
                                    images_html += f'<img src="images/{img_name}" alt="{title}">\n'
                                except Exception as e:
                                    logging.error(f"이미지 다운로드 실패: {str(e)}")
                        
                        # HTML 파일 저장
                        saved_file = save_article(
                            title, 
                            content.get_text(strip=True), 
                            images_html,
                            base_path
                        )
                        
                        logging.info(f'Successfully saved: {saved_file}')
                    
                    time.sleep(random.uniform(2, 4))
                    
                except Exception as e:
                    logging.error(f'Error processing article: {str(e)}')
                    continue
            
            page += 1
            time.sleep(random.uniform(3, 5))
            
    except Exception as e:
        logging.error(f'Error occurred: {str(e)}')

if __name__ == '__main__':
    print('Starting to scrape humorworld.net category...')
    scrape_category()
    print('Scraping completed!')
