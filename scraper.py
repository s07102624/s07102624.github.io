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
    base_path = os.path.join('s07102624.github.io', 'output', '2025')
    image_path = os.path.join(base_path, 'images')
    
    # 폴더 생성
    os.makedirs(base_path, exist_ok=True)
    os.makedirs(image_path, exist_ok=True)
    
    return base_path, image_path

def save_article(title, content, images, base_path, prev_post=None, next_post=None):
    """HTML 파일로 게시물 저장"""
    try:
        safe_title = clean_filename(title)
        filename = os.path.join(base_path, f'{safe_title}.html')
        
        logging.info(f"Saving HTML file: {filename}")
        
        # 원본 컨텐츠에서 HTML 구조 유지
        content_html = str(content) if isinstance(content, BeautifulSoup) else content
        
        html_content = f"""<!DOCTYPE html>
<html lang="ko-KR" class="js">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title>
    <link rel="stylesheet" href="https://humorworld.net/wp-content/themes/blogberg/style.css">
</head>
<body class="post-template-default single single-post">
    <div id="page" class="site">
        <div id="content" class="site-content">
            <div class="container">
                <div id="primary" class="content-area">
                    <main id="main" class="site-main">
                        <article class="post format-standard hentry">
                            <header class="entry-header">
                                <h1 class="entry-title">{title}</h1>
                            </header>
                            <div class="entry-content">
                                {content_html}
                                {images}
                            </div>
                            <footer class="entry-footer">
                                <nav class="navigation post-navigation">
                                    <div class="nav-links">
                                        {f'<div class="nav-previous"><a href="{prev_post["filename"]}">{prev_post["title"]}</a></div>' if prev_post else ''}
                                        {f'<div class="nav-next"><a href="{next_post["filename"]}">{next_post["title"]}</a></div>' if next_post else ''}
                                    </div>
                                </nav>
                            </footer>
                        </article>
                    </main>
                </div>
            </div>
        </div>
    </div>
</body>
</html>"""
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logging.info(f"Successfully saved HTML file: {filename}")
        return filename
    except Exception as e:
        logging.error(f"Error saving HTML file: {str(e)}")
        return None

def is_duplicate_post(title, base_path):
    """게시물 제목 중복 검사"""
    safe_title = clean_filename(title)
    return os.path.exists(os.path.join(base_path, f'{safe_title}.html'))

def scrape_category():
    """게시물 스크래핑 함수"""
    base_path, image_path = setup_folders()
    posts_info = []
    post_count = 0
    base_url = 'https://humorworld.net/category/humorstorage/'
    
    try:
        scraper = get_scraper()
        page = 1
        
        while True:
            url = f'{base_url}page/{page}/' if page > 1 else base_url
            logging.info(f"Scraping page {page}: {url}")
            
            response = scraper.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            articles = soup.select('article.format-standard')
            if not articles:
                logging.info("No more articles found")
                break
                
            for article in articles:
                try:
                    title_elem = article.select_one('.entry-title a')
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    link = title_elem.get('href')
                    
                    # 중복 게시물 검사
                    if is_duplicate_post(title, base_path):
                        logging.info(f"Skipping duplicate post: {title}")
                        continue
                    
                    # 게시물 상세 페이지 스크래핑
                    article_response = scraper.get(link)
                    article_soup = BeautifulSoup(article_response.text, 'html.parser')
                    
                    content = article_soup.select_one('.entry-content')
                    if not content:
                        logging.error(f"Content not found for: {title}")
                        continue

                    # 이미지 처리
                    images_html = ""
                    for img in content.find_all('img'):
                        if img.get('src'):
                            img_name = clean_filename(os.path.basename(img['src']))
                            img_path = os.path.join(image_path, img_name)
                            
                            try:
                                img_response = scraper.get(img['src'])
                                with open(img_path, 'wb') as f:
                                    f.write(img_response.content)
                                images_html += f'<img src="images/{img_name}" alt="{title}">\n'
                                logging.info(f"Image saved: {img_name}")
                            except Exception as e:
                                logging.error(f"Failed to download image: {str(e)}")

                    # 게시물 저장 직접 수행
                    saved_file = save_article(
                        title,
                        content,  # BeautifulSoup 객체 그대로 전달
                        images_html,
                        base_path
                    )
                    
                    if saved_file:
                        logging.info(f"Article saved: {title}")
                        post_count += 1
                    
                    if post_count % 10 == 0:
                        choice = input(f"\n{post_count}개의 게시물을 스크래핑했습니다. 계속하시겠습니까? (y/n): ")
                        if choice.lower() != 'y':
                            return
                    
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
