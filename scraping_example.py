import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import urllib.parse
from datetime import datetime
import json
import hashlib
import schedule
import logging
import sqlite3
from datetime import datetime, timedelta
import socket
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def setup_logging():
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, f'scraper_{datetime.now().strftime("%Y%m%d")}.log')),
            logging.StreamHandler()
        ]
    )

def setup_database():
    with sqlite3.connect('scraper.db') as conn:
        conn.execute('''
        CREATE TABLE IF NOT EXISTS visitor_logs (
            ip_address TEXT PRIMARY KEY,
            last_visit TIMESTAMP
        )''')
        
        conn.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            post_id TEXT PRIMARY KEY,
            title TEXT,
            link TEXT,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

def check_ip_visited(ip_address):
    try:
        with sqlite3.connect('visitor_logs.db') as conn:
            cur = conn.cursor()
            cur.execute('SELECT last_visit FROM visitor_logs WHERE ip_address = ?', (ip_address,))
            result = cur.fetchone()
            
            current_time = datetime.now()
            if result is None:
                cur.execute('INSERT INTO visitor_logs VALUES (?, ?)', (ip_address, current_time))
                return False
            
            last_visit = datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S.%f')
            if (current_time - last_visit).days >= 1:
                cur.execute('UPDATE visitor_logs SET last_visit = ? WHERE ip_address = ?', 
                          (current_time, ip_address))
                return False
            
            return True
    except Exception as e:
        logging.error(f"IP 체크 중 오류: {str(e)}")
        return False

def is_post_exists(post_id):
    try:
        with sqlite3.connect('scraper.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM posts WHERE post_id = ?', (post_id,))
            return cursor.fetchone() is not None
    except Exception as e:
        logging.error(f"중복 체크 중 오류: {str(e)}")
        return False

def save_post_to_db(post_data):
    try:
        with sqlite3.connect('scraper.db') as conn:
            cursor = conn.cursor()
            post_id = hashlib.md5(post_data['link'].encode()).hexdigest()
            
            if not is_post_exists(post_id):
                cursor.execute('''
                INSERT INTO posts (post_id, title, link, content)
                VALUES (?, ?, ?, ?)
                ''', (post_id, post_data['title'], post_data['link'], post_data['content']))
                return True
        return False
    except Exception as e:
        logging.error(f"게시글 저장 중 오류: {str(e)}")
        return False

def download_media(url, folder):
    try:
        if not os.path.exists(folder):
            os.makedirs(folder)
            
        # 파일명 생성
        filename = os.path.join(folder, hashlib.md5(url.encode()).hexdigest() + os.path.splitext(url)[1])
        
        # 이미 다운로드된 파일이면 스킵
        if os.path.exists(filename):
            return filename
            
        # 파일 다운로드
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return filename
    except Exception as e:
        print(f"미디어 다운로드 실패: {url} - {str(e)}")
    return None

def save_to_html(posts_data, page_number):
    output_dir = os.path.join("output", datetime.now().strftime("%Y%m%d"))
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    html_file = os.path.join(output_dir, f"humorworld_page_{page_number}_{datetime.now().strftime('%H%M%S')}.html")
    
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write('''
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>HumorWorld 스크래핑 결과</title>
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-9374368296307755"
     crossorigin="anonymous"></script>
    <script async src="js/ads.js"></script>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .post { border: 1px solid #ddd; margin: 20px 0; padding: 15px; border-radius: 5px; }
        .title { font-size: 1.2em; color: #333; }
        .content { color: #666; margin: 10px 0; }
        img { max-width: 100%; height: auto; margin: 10px 0; }
        video { max-width: 100%; margin: 10px 0; }
        .ad-container { margin: 20px 0; text-align: center; }
        .popup { display: none; position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
                background: white; padding: 20px; box-shadow: 0 0 10px rgba(0,0,0,0.5); z-index: 1000; }
        .overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                  background: rgba(0,0,0,0.5); z-index: 999; }
    </style>
</head>
<body>
    <div id="overlay" class="overlay"></div>
    <div id="adPopup" class="popup">
        <div id="timer">7</div>
        <div id="popupAdContainer">
            <!-- 보험 팝업 -->
            <ins class="adsbygoogle popup-ad"
                 style="display:block"
                 data-ad-client="ca-pub-9374368296307755"
                 data-ad-slot="8384240134"
                 data-ad-format="auto"
                 data-full-width-responsive="true"></ins>
        </div>
        <button id="closeBtn" disabled>닫기 (<span id="timer">7</span>초)</button>
    </div>
    
    <div class="ad-container">
        <!-- 상단 광고 -->
        <ins class="adsbygoogle"
             style="display:block"
             data-ad-client="ca-pub-9374368296307755"
             data-ad-slot="8384240134"
             data-ad-format="auto"
             data-full-width-responsive="true"></ins>
        <script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
    </div>
        ''')
        
        for post in posts_data:
            f.write(f'''
    <div class="post">
        <div class="title"><a href="{post['link']}">{post['title']}</a></div>
        <div class="content">{post['content']}</div>
        ''')
            
            if post.get('images'):
                for img in post['images']:
                    f.write(f'        <img src="{img}" alt="스크래핑 이미지">\n')
            
            if post.get('videos'):
                for video in post['videos']:
                    f.write(f'        <video controls src="{video}"></video>\n')
            
            f.write('    </div>\n')
        
        f.write('''
    <div class="ad-container">
        <!-- 하단 광고 -->
        <ins class="adsbygoogle"
             style="display:block"
             data-ad-client="ca-pub-YOUR_ID"
             data-ad-slot="YOUR_SLOT_ID"
             data-ad-format="auto"
             data-full-width-responsive="true"></ins>
        <script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
    </div>
    
    <script>
        function showPopup() {
            if (!localStorage.getItem('popupShown')) {
                document.getElementById('overlay').style.display = 'block';
                document.getElementById('popup').style.display = 'block';
                localStorage.setItem('popupShown', 'true');
            }
        }
        
        function closePopup() {
            document.getElementById('overlay').style.display = 'none';
            document.getElementById('popup').style.display = 'none';
        }
        
        window.onload = showPopup;
    </script>
</body>
</html>
        ''')
    
    print(f"HTML 파일이 생성되었습니다: {html_file}")

def scrape_with_requests():
    print("\n=== HumorWorld 게시글 스크래핑 (BeautifulSoup) ===")
    url = "https://www.humorworld.net/?cat=1"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache"
    }
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            posts = soup.select("article.post")
            
            if not posts:
                print("게시글을 찾을 수 없습니다. Selenium으로 시도합니다.")
                return
                
            for post in posts[:10]:
                title_elem = post.select_one(".entry-title")
                content_elem = post.select_one(".entry-content")
                link_elem = post.select_one(".entry-title a")
                
                if title_elem and link_elem:
                    title = title_elem.get_text().strip()
                    link = link_elem.get('href', '')
                    content = content_elem.get_text().strip()[:100] if content_elem else "내용 없음"
                    print(f"제목: {title}")
                    print(f"링크: {link}")
                    print(f"내용: {content}...\n")
        else:
            print("페이지 로드 실패:", response.status_code)
    except Exception as e:
        print(f"에러 발생 ({type(e).__name__}): {str(e)}")

def scrape_with_selenium():
    print("\n=== HumorWorld 게시글 스크래핑 (Selenium) ===")
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--enable-unsafe-swiftshader")  # WebGL 오류 해결
    options.add_argument('--window-size=1920,1080')
    options.add_argument(f"user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36")
    
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        base_url = "https://www.humorworld.net/?cat=1&paged={}"
        page = 1
        while page <= 5:  # 최대 5페이지까지 스크래핑
            current_url = base_url.format(page)
            driver.get(current_url)
            time.sleep(5)
            
            posts = driver.find_elements(By.CSS_SELECTOR, "article.post")
            posts_data = []
            new_posts_count = 0
            
            media_folder = "downloaded_media"
            
            for post in posts:
                try:
                    post_data = {
                        'title': post.find_element(By.CSS_SELECTOR, ".entry-title").text.strip(),
                        'link': post.find_element(By.CSS_SELECTOR, ".entry-title a").get_attribute('href'),
                        'content': post.find_element(By.CSS_SELECTOR, ".entry-content").text.strip()[:200],
                        'images': [],
                        'videos': []
                    }
                    
                    # 중복 체크 후 저장
                    if save_post_to_db(post_data):
                        new_posts_count += 1
                        
                        # 이미지 찾기
                        images = post.find_elements(By.CSS_SELECTOR, "img")
                        for img in images:
                            img_url = img.get_attribute('src')
                            if img_url:
                                saved_path = download_media(img_url, os.path.join(media_folder, 'images'))
                                if saved_path:
                                    post_data['images'].append(saved_path)
                        
                        # 비디오 찾기
                        videos = post.find_elements(By.CSS_SELECTOR, "video source, iframe")
                        for video in videos:
                            video_url = video.get_attribute('src')
                            if video_url:
                                saved_path = download_media(video_url, os.path.join(media_folder, 'videos'))
                                if saved_path:
                                    post_data['videos'].append(saved_path)
                        
                        posts_data.append(post_data)
                        print(f"제목: {post_data['title']}")
                        print(f"링크: {post_data['link']}")
                        print(f"내용: {post_data['content']}...\n")
                        
                except Exception as e:
                    logging.error(f"게시글 파싱 중 오류: {str(e)}")
                    continue
            
            if posts_data:
                save_to_html(posts_data, page)
                logging.info(f"페이지 {page}: 새로운 게시글 {new_posts_count}개 저장")
            
            if new_posts_count == 0:
                logging.info("새로운 게시글이 없어 스크래핑 종료")
                break
                
            page += 1
                
    except Exception as e:
        print(f"에러 발생 ({type(e).__name__}): {str(e)}")
    finally:
        driver.quit()

def run_scraper():
    logging.info("스크래핑 작업 시작")
    try:
        scrape_with_selenium()
        logging.info("스크래핑 작업 완료")
    except Exception as e:
        logging.error(f"스크래핑 중 오류 발생: {str(e)}")

def main():
    setup_logging()
    setup_database()
    logging.info("스크래퍼 초기화")
    
    # 커맨드 라인 인자 확인
    if len(sys.argv) > 1 and sys.argv[1] == "manual":
        logging.info("수동 실행 모드")
        run_scraper()
        return
    
    # 자동 실행 모드
    schedule.every().day.at("21:00").do(run_scraper)
    
    logging.info("스케줄러 시작 - 매일 저녁 9시 실행")
    print("스크래퍼가 실행 중입니다. Ctrl+C로 종료할 수 있습니다.")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        logging.info("스크래퍼 종료")
        print("\n스크래퍼를 종료합니다.")

if __name__ == "__main__":
    main()
