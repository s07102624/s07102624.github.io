import sys
import io
import sqlite3
import json
import requests  # requests 모듈 추가
import hashlib
from urllib.parse import urlparse  # urlparse 함수 추가
from scraping_example import (
    setup_logging, setup_database, save_post_to_db, 
    download_media, save_to_html, Options, webdriver, 
    Service, ChromeDriverManager, By, logging, time, os
)
from selenium.webdriver.chrome.service import Service as ChromeService  # 수정된 import
from PIL import Image  # Pillow 라이브러리 추가

# 새로운 imports 추가
try:
    from bs4 import BeautifulSoup
    import cloudscraper
    from fake_useragent import UserAgent
except ImportError as e:
    print(f"필요한 패키지가 설치되지 않았습니다: {str(e)}")
    print("다음 명령어로 필요한 패키지를 설치하세요:")
    print("pip install beautifulsoup4 cloudscraper fake-useragent")
    sys.exit(1)

import random

# UTF-8 인코딩 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
if sys.stderr.encoding != 'utf-8':
    sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)

def replace_text_content(html_content, title):
    # 기존 텍스트를 게시글 제목으로 변경
    html_content = html_content.replace('유머월드', title)
    html_content = html_content.replace('humorworld', title.lower())
    return html_content

def shift_posts(output_dir):
    """기존 파일들을 한 단계씩 뒤로 이동"""
    files = sorted([f for f in os.listdir(output_dir) if f.endswith('.html')], 
                  key=lambda x: int(x.split('.')[0]), reverse=True)
    
    for file in files:
        current_num = int(file.split('.')[0])
        new_name = f"{current_num + 1}.html"
        os.rename(os.path.join(output_dir, file), 
                 os.path.join(output_dir, new_name))

def save_html_file(page_num, html_content, posts_data=None):
    # 경로 수정
    output_dir = os.path.join('s07102624.github.io', 'output', '1004')
    os.makedirs(output_dir, exist_ok=True)
    
    if posts_data:
        # DB 연결
        conn = sqlite3.connect('posts.db')
        cursor = conn.cursor()
        
        # 테이블 생성
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            images TEXT,
            videos TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            hash TEXT
        )
        ''')
        
        # 게시물들 저장
        for post in posts_data:
            cursor.execute(
                'INSERT INTO posts (title, content, images, videos, hash) VALUES (?, ?, ?, ?, ?)',
                (
                    post['title'],
                    post['content'],
                    json.dumps(post.get('images', [])),
                    json.dumps(post.get('videos', [])),
                    post['hash']
                )
            )
        
        conn.commit()
        conn.close()
    
    # HTML 내용 변경 (title 파라미터 추가)
    html_content = replace_text_content(html_content, posts_data[0]['title'] if posts_data else 'Default Title')
    
    file_path = os.path.join(output_dir, f'{page_num}.html')
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

def save_to_html(post_data, page_num):
    # HTML 템플릿 수정 - 제목을 게시글 제목으로 변경
    html_template = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <title>{post_data['title']} - {page_num}페이지</title>
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
        <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-9374368296307755" crossorigin="anonymous"></script>
        <style>
            body {{
                font-family: -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Oxygen-Sans,Ubuntu,Cantarell,"Helvetica Neue",sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 10px;
                background: #f0f2f5;
            }}
            .content {{
                width: 100%;
                max-width: 800px;
                margin: 0 auto;
                background: #fff;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 1px 2px rgba(0,0,0,0.1);
                box-sizing: border-box;
            }}
            .preview {{
                border-bottom: 1px solid #eee;
                padding: 15px 0;
                display: grid;
                grid-template-columns: 1fr;
                gap: 15px;
            }}
            .preview-media {{
                width: 100%;
                aspect-ratio: 16/9;
                overflow: hidden;
                border-radius: 8px;
            }}
            .preview-media img {{
                width: 100%;
                height: 100%;
                object-fit: cover;
            }}
            .preview-content {{
                display: flex;
                flex-direction: column;
                gap: 10px;
            }}
            .preview-content h2 {{
                margin: 0;
                font-size: 1.2em;
                color: #333;
                word-break: break-all;
            }}
            .full-content {{
                margin-top: 15px;
            }}
            .full-content img {{
                width: 100%;
                max-width: 100%;
                height: auto;
                margin: 10px 0;
                border-radius: 4px;
            }}
            @media (min-width: 768px) {{
                .preview {{
                    grid-template-columns: 300px 1fr;
                }}
                .preview-media {{
                    aspect-ratio: 4/3;
                }}
            }}
            .preview .content {{
                margin: 10px 0;
                color: #666;
                padding: 0;
                box-shadow: none;
                font-size: 0.95em;
                word-break: break-all;
            }}
            .preview img {{
                display: block;
                width: 100%;
                max-width: 100%;
                height: auto;
                margin: 10px auto;
                border-radius: 4px;
            }}
            .preview video {{
                display: block;
                width: 100%;
                max-width: 100%;
                height: auto;
                margin: 10px auto;
                border-radius: 4px;
            }}
            .ad-container {{
                margin: 15px 0;
                text-align: center;
                overflow: hidden;
            }}
            @media screen and (max-width: 600px) {{
                body {{
                    padding: 5px;
                }}
                .content {{
                    padding: 10px;
                }}
                .preview h2 {{
                    font-size: 1.1em;
                }}
                .preview .content {{
                    font-size: 0.9em;
                }}
            }}
            .popup {{
                display: none;
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 0 10px rgba(0,0,0,0.5);
                z-index: 1000;
            }}
            .overlay {{
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.5);
                z-index: 999;
            }}
            #timer {{
                text-align: center;
                margin-bottom: 10px;
            }}
            #closeBtn {{
                display: block;
                width: 100%;
                padding: 10px;
                margin-top: 10px;
                border: none;
                border-radius: 4px;
                background: #007bff;
                color: white;
                cursor: pointer;
            }}
            #closeBtn:disabled {{
                background: #ccc;
            }}
        </style>
    </head>
    <body>
        <div id="overlay" class="overlay"></div>
        <div id="adPopup" class="popup">
            <div id="timer">7</div>
            <div id="popupAdContainer">
                <!-- 보험 팝업 광고 -->
                <ins class="adsbygoogle"
                     style="display:block"
                     data-ad-client="ca-pub-9374368296307755"
                     data-ad-slot="8384240134"
                     data-ad-format="auto"
                     data-full-width-responsive="true"></ins>
            </div>
            <button id="closeBtn" disabled>닫기 (<span id="timerText">7</span>초)</button>
        </div>

        <div class="content">
            <h1>테스트프로 - 페이지 {page_num}</h1>

            <!-- 상단 광고 -->
            <div class="ad-container">
                <ins class="adsbygoogle"
                     style="display:block"
                     data-ad-client="ca-pub-9374368296307755"
                     data-ad-slot="8384240134"
                     data-ad-format="auto"
                     data-full-width-responsive="true"></ins>
                <script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>
            </div>
    """

    html_template += f"""
    <div class="navigation">
        <a href="{page_num-1}.html" {"style='visibility:hidden'" if page_num == 1 else ""}>← 이전 글</a>
        <a href="index.html">목록으로</a>
        <a href="{page_num+1}.html">다음 글 →</a>
    </div>
    
    <div class="preview">
        <!-- 이미지를 먼저 표시하도록 순서 변경 -->
        <div class="preview-media">
            {' '.join([f'<img src="{img_path}" alt="이미지" loading="lazy">' for img_path in post_data['images'][:1]])}
        </div>
        <div class="preview-content">
            <h2>{post_data['title']}</h2>
            <div class="content">{post_data['content']}</div>
        """
    
    # 이미지와 비디오 처리
    for img_path in post_data['images']:
        html_template += f'<img src="{img_path}" alt="이미지">\n'
        
    # 비디오 처리 부분 수정
    for video_path in post_data['videos']:
        if 'youtube.com' in video_path or 'youtu.be' in video_path:
            video_id = extract_youtube_id(video_path)
            if video_id:
                html_template += f'''
                <div class="video-container">
                    <iframe 
                        src="https://www.youtube.com/embed/{video_id}"
                        title="YouTube video player"
                        frameborder="0"
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                        allowfullscreen>
                    </iframe>
                </div>
                '''
        elif video_path.endswith(('.mp4', '.webm', '.ogg')):
            html_template += f'<video controls src="{video_path}"></video>\n'

    html_template += """
            <!-- 하단 광고 -->
            <div class="ad-container">
                <ins class="adsbygoogle"
                     style="display:block"
                     data-ad-client="ca-pub-9374368296307755"
                     data-ad-slot="8384240134"
                     data-ad-format="auto"
                     data-full-width-responsive="true"></ins>
                <script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
            </div>
        </div>

        <script>
            function getCookie(name) {
                const value = `; ${document.cookie}`;
                const parts = value.split(`; ${name}=`);
                if (parts.length === 2) return parts.pop().split(';').shift();
            }

            function setCookie(name, value, days) {
                const date = new Date();
                date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
                document.cookie = `${name}=${value};expires=${date.toUTCString()};path=/`;
            }

            function showPopup() {
                if (!getCookie('popupShown')) {
                    document.getElementById('overlay').style.display = 'block';
                    document.getElementById('adPopup').style.display = 'block';
                    
                    let timeLeft = 7;
                    const timer = setInterval(() => {
                        timeLeft--;
                        document.getElementById('timer').textContent = timeLeft;
                        document.getElementById('timerText').textContent = timeLeft;
                        
                        if (timeLeft <= 0) {
                            clearInterval(timer);
                            document.getElementById('closeBtn').disabled = false;
                            document.getElementById('closeBtn').textContent = '닫기';
                        }
                    }, 1000);

                    setCookie('popupShown', 'true', 1);
                    (adsbygoogle = window.adsbygoogle || []).push({});
                }
            }

            document.getElementById('closeBtn').onclick = function() {
                document.getElementById('overlay').style.display = 'none';
                document.getElementById('adPopup').style.display = 'none';
            };

            window.addEventListener('load', showPopup);
            (adsbygoogle = window.adsbygoogle || []).push({});
        </script>
    </body>
    </html>
    """

    save_html_file(page_num, html_template, [post_data])

def extract_youtube_id(url):
    if not url:
        return None
    if 'youtu.be/' in url:
        return url.split('youtu.be/')[-1].split('?')[0]
    elif 'youtube.com/embed/' in url:
        return url.split('embed/')[-1].split('?')[0]
    elif 'watch?v=' in url:
        return url.split('watch?v=')[-1].split('&')[0]
    return None

def update_index_file(total_pages):
    """인덱스 파일 업데이트"""
    index_template = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>테스트프로 인덱스</title>
    <style>
        body {
            font-family: -apple-system, system-ui, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background: #f0f2f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #fff;
            border-radius: 8px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }
        .page-list {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 10px;
            margin: 20px 0;
        }
        .page-list a {
            display: block;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 4px;
            text-decoration: none;
            color: #333;
            text-align: center;
        }
        .page-list a:hover {
            background: #e9ecef;
        }
        .pagination {
            display: flex;
            justify-content: center;
            gap: 5px;
            margin-top: 20px;
        }
        .pagination button {
            padding: 8px 12px;
            border: none;
            background: #f8f9fa;
            cursor: pointer;
            border-radius: 4px;
        }
        .pagination button:hover {
            background: #e9ecef;
        }
        .pagination button.active {
            background: #007bff;
            color: white;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>테스트프로 페이지 목록</h1>
        <div class="page-list" id="pageList">
"""
    
    # 페이지 링크 생성 부분 수정
    for i in range(1, total_pages + 1):
        index_template += f'            <a href="s07102624.github.io/output/1004/{i}.html">페이지 {i}</a>\n'
    
    index_template += """
        </div>
        <div class="pagination" id="pagination"></div>
    </div>
    <script>
        const itemsPerPage = 1; // 한 페이지당 1개씩 표시
        const pageList = document.getElementById('pageList');
        const pagination = document.getElementById('pagination');
        const links = pageList.getElementsByTagName('a');
        
        function showPage(pageNum) {
            // 모든 링크 숨기기
            for (let i = 0; i < links.length; i++) {
                links[i].style.display = 'none';
            }
            
            // 현재 페이지 링크만 표시
            const current = pageNum - 1;
            if (links[current]) {
                links[current].style.display = 'block';
            }
            
            updatePagination(pageNum);
        }
        
        function updatePagination(currentPage) {
            const totalPages = links.length;
            let html = '';
            
            // 이전 버튼
            if (currentPage > 1) {
                html += `<button onclick="showPage(${currentPage - 1})">이전</button>`;
            }
            
            // 현재 페이지
            html += `<button class="active">${currentPage} / ${totalPages}</button>`;
            
            // 다음 버튼
            if (currentPage < totalPages) {
                html += `<button onclick="showPage(${currentPage + 1})">다음</button>`;
            }
            
            pagination.innerHTML = html;
        }
        
        // 초기 페이지 표시
        showPage(1);
    </script>
</body>
</html>
"""
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(index_template)

def download_media(url, folder):
    """미디어 다운로드 함수 - WebP 지원 추가"""
    try:
        if not url or 'data:' in url:
            return None
            
        # 이미지 저장 경로 수정
        image_dir = os.path.join('s07102624.github.io', 'output', '1004', 'images')
        os.makedirs(image_dir, exist_ok=True)
        
        # 파일명 생성
        base_name = os.path.splitext(os.path.basename(url.split('?')[0]))[0]
        filename = os.path.join(image_dir, f"{base_name}.webp")
        
        # User-Agent 헤더 추가
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36',
            'Referer': 'https://www.humorworld.net/'
        }
        
        # 최대 3번 재시도
        for attempt in range(3):
            try:
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                
                # 이미지인 경우 WebP로 변환
                if any(url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif']):
                    img = Image.open(io.BytesIO(response.content))
                    # RGBA 모드인 경우 RGB로 변환
                    if img.mode in ('RGBA', 'LA'):
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        background.paste(img, mask=img.split()[-1])
                        img = background
                    # WebP로 저장 (품질 85%)
                    img.save(filename, 'WEBP', quality=85)
                else:
                    # 비디오 등 다른 미디어는 그대로 저장
                    with open(filename, 'wb') as f:
                        f.write(response.content)
                
                # 상대 경로 반환 (HTML에서 참조할 경로)
                return os.path.join('images', f"{base_name}.webp")
                
            except requests.exceptions.RequestException as e:
                print(f"다운로드 실패 (시도 {attempt + 1}/3): {url}\n에러: {str(e)}")
                if attempt == 2:
                    return None
                time.sleep(2)
                
    except Exception as e:
        print(f"미디어 다운로드 중 에러 발생: {str(e)}")
        return None

def is_post_exists(post_hash):
    """게시물 중복 체크"""
    try:
        conn = sqlite3.connect('posts.db')
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM posts WHERE hash = ?', (post_hash,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists
    except Exception as e:
        logging.error(f"게시물 중복 체크 중 오류: {str(e)}")
        return False

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
    # 헤더 별도 설정
    scraper.headers.update({
        'User-Agent': ua.random,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://www.humorworld.net/',
        'DNT': '1',
    })
    return scraper

def get_post_detail(scraper, url):
    """게시물 상세 페이지 스크래핑"""
    try:
        time.sleep(random.uniform(2, 4))  # 대기 시간
        response = scraper.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 상세 내용 추출
        article = soup.select_one('article')
        if not article:
            return None
            
        content = article.select_one('.entry-content')
        if not content:
            return None
            
        # 전체 내용 텍스트
        full_content = content.get_text(strip=True)
        
        # 이미지 목록
        images = content.select('img')
        image_urls = []
        for img in images:
            src = img.get('src', '') or img.get('data-src', '')
            if src:
                if not urlparse(src).netloc:
                    src = f"https://www.humorworld.net{src}"
                image_urls.append(src)
                
        # 비디오 목록
        videos = content.select('iframe[src*="youtube.com"], iframe[src*="youtu.be"]')
        video_urls = [v.get('src', '') for v in videos if v.get('src')]
        
        return {
            'content': full_content,
            'images': image_urls,
            'videos': video_urls
        }
        
    except Exception as e:
        print(f"상세 페이지 스크래핑 중 오류: {str(e)}")
        return None

def generate_clickbait_title(original_title):
    """클릭을 유도하는 제목으로 변경"""
    clickbait_prefixes = [
        "충격) ", "경악) ", "기절) ", "초대박) ", "전설의 ", "역대급 ", "실화) ", 
        "개쩌는 ", "핵심) ", "급발진) ", "대박) ", "놀라운) ", "속보) ", "극찬) ",
        "화제의 ", "완전 ", "레전드 ", "반전) ", "감동) ", "최초) ", "단독) ",
        "충격적) ", "심장주의) ", "긴급) ", "초강력 ", "핫이슈) ", "폭발) ",
        "공감) ", "경이로운 ", "엄청난 ", "초특급 ", "초고급 ", "무서운 ",
        "놀라워) ", "신기한 ", "미쳤다) ", "기가막힌 ", "대단한 ", "끝판왕 ",
        "무한대박 "
    ]
    
    clickbait_suffixes = [
        " (진짜 충격적)", " (대박사건)", " (완전 실화)", " (믿을 수 없음)", 
        " (역대급)", " (레전드)", " (핵심 요약)", " (현실 상황)", " (심장 주의)", 
        " (꼭 봐야함)", " (실화임)", " (진짜임)", " (충격 반전)", " (진실 공개)",
        " (완전 대박)", " (전설급)", " (극한 상황)", " (절대 놓치지 마세요)", 
        " (눈물 주의)", " (감동 실화)", " (충격적 진실)", " (공감 100%)",
        " (신기함 주의)", " (반전 엔딩)", " (극한 상황)", " (완전 실화임)",
        " (기적 같은)", " (놀라운 결과)", " (충격과 공포)", " (진실 폭로)",
        " (필독)", " (초강력)", " (폭소 주의)", " (극비 공개)", " (경악)",
        " (충격 실화)", " (동공지진)", " (화제의 그것)", " (완전 소름)",
        " (기가 막힘)"
    ]
    
    # 50% 확률로 접두어 추가
    if random.random() < 0.5:
        prefix = random.choice(clickbait_prefixes)
    else:
        prefix = ""
        
    # 50% 확률로 접미어 추가
    if random.random() < 0.5:
        suffix = random.choice(clickbait_suffixes)
    else:
        suffix = ""
        
    return f"{prefix}{original_title}{suffix}"

def infinite_scrape():
    print("\n=== HumorWorld 전체 게시글 스크래핑 시작 ===")
    
    try:
        scraper = get_scraper()
    except Exception as e:
        print(f"스크래퍼 초기화 중 오류 발생: {str(e)}")
        print("일반 requests 세션으로 대체합니다...")
        scraper = requests.Session()
        scraper.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://www.humorworld.net/',
            'Cookie': 'wordpress_test_cookie=WP%20Cookie%20check'
        })
    
    base_url = "https://www.humorworld.net/?cat=1&paged={}"
    page = 1
    total_posts = 0
    
    try:
        while True:
            current_url = base_url.format(page)
            print(f"\n=== 페이지 {page} 스크래핑 중... ===")
            
            try:
                response = scraper.get(current_url)
                response.raise_for_status()
                
                # 디버그: HTML 내용 확인
                print(f"응답 상태 코드: {response.status_code}")
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 게시물 찾기 - 수정된 선택자
                posts = soup.select('article.format-standard')
                
                print(f"발견된 게시물 수: {len(posts)}")
                
                if not posts:
                    print("\n페이지 구조 분석:")
                    print(soup.select('article'))  # 디버그용
                    if page > 1:
                        print("\n더 이상 게시글이 없습니다.")
                        break
                    else:
                        print("\n게시글을 찾을 수 없습니다.")
                        continue
                
                for post in posts:
                    try:
                        # 게시물 링크 찾기
                        title_elem = post.select_one('.entry-title a')
                        if not title_elem:
                            continue
                            
                        post_url = title_elem.get('href')
                        if not post_url:
                            continue
                            
                        # 상세 페이지 스크래핑
                        print(f"\n상세 페이지 스크래핑 중: {post_url}")
                        detail_data = get_post_detail(scraper, post_url)
                        
                        if not detail_data:
                            print("상세 페이지 스크래핑 실패")
                            continue
                        
                        # 게시물 데이터 구성 부분 수정
                        post_data = {
                            'title': generate_clickbait_title(title_elem.get_text(strip=True)),
                            'content': detail_data['content'],
                            'images': [],
                            'videos': detail_data['videos'],
                            'hash': hashlib.md5((title_elem.get_text(strip=True) + detail_data['content']).encode('utf-8')).hexdigest()
                        }
                        
                        # 이미지 다운로드
                        for img_url in detail_data['images']:
                            saved_path = download_media(img_url, os.path.join('s07102624.github.io', 'output', '1004', 'images'))
                            if saved_path:
                                post_data['images'].append(saved_path)
                        
                        # HTML 파일 저장
                        save_to_html(post_data, page)
                        total_posts += 1
                        
                        print(f"\n성공적으로 스크래핑된 게시물:")
                        print(f"제목: {post_data['title']}")
                        print(f"내용 길이: {len(post_data['content'])} 글자")
                        print(f"이미지 수: {len(post_data['images'])}")
                        print(f"비디오 수: {len(post_data['videos'])}")
                        
                    except Exception as e:
                        print(f"게시글 파싱 중 오류: {str(e)}")
                        continue
                
                # 다음 페이지로
                page += 1
                update_index_file(page-1)
                
                # 사용자 입력 확인 (5페이지마다)
                if page % 5 == 0:
                    choice = input(f"\n현재 {total_posts}개의 게시글을 스크래핑했습니다. 계속하시겠습니까? (y/n): ")
                    if choice.lower() != 'y':
                        break
                
            except Exception as e:
                print(f"페이지 스크래핑 중 오류 발생: {str(e)}")
                print(f"URL: {current_url}")
                time.sleep(random.uniform(10, 15))  # 오류 발생시 더 긴 대기 시간
                continue
            
    except KeyboardInterrupt:
        print("\n\n사용자가 중단했습니다.")
    except Exception as e:
        print(f"예상치 못한 오류 발생: {str(e)}")
    finally:
        print(f"\n총 {total_posts}개의 게시글을 스크래핑했습니다.")

if __name__ == "__main__":
    setup_logging()
    setup_database()
    infinite_scrape()
