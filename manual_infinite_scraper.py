import sys
import io
import sqlite3
import json
import requests  # requests 모듈 추가
from urllib.parse import urlparse  # urlparse 함수 추가
from scraping_example import (
    setup_logging, setup_database, save_post_to_db, 
    download_media, save_to_html, Options, webdriver, 
    Service, ChromeDriverManager, By, logging, time, os
)

# UTF-8 인코딩 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
if sys.stderr.encoding != 'utf-8':
    sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)

def replace_text_content(html_content):
    # HTML 내용에서 "유머월드" 텍스트를 "테스트프로"로 변경
    html_content = html_content.replace('유머월드', '테스트프로')
    html_content = html_content.replace('humorworld', 'testpro')
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
    output_dir = os.path.join('output', '20250307')
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 게시물들 저장
        for post in posts_data:
            cursor.execute(
                'INSERT INTO posts (title, content, images, videos) VALUES (?, ?, ?, ?)',
                (
                    post['title'],
                    post['content'],
                    json.dumps(post.get('images', [])),
                    json.dumps(post.get('videos', []))
                )
            )
        
        conn.commit()
        conn.close()
    
    # HTML 내용 변경
    html_content = replace_text_content(html_content)
    
    file_path = os.path.join(output_dir, f'{page_num}.html')
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

def save_to_html(post_data, page_num):
    # 단일 post_data를 받도록 수정
    html_template = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <title>테스트프로 {page_num}페이지</title>
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
            }}
            .preview h2 {{
                margin: 0 0 10px 0;
                font-size: 1.2em;
                color: #333;
                word-break: break-all;
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
    
    # 페이지 링크 생성
    for i in range(1, total_pages + 1):
        index_template += f'            <a href="output/20250307/{i}.html">페이지 {i}</a>\n'
    
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
    """미디어 다운로드 함수 개선"""
    try:
        # URL 검증
        if not url or 'data:' in url:
            return None
            
        # 폴더 생성
        os.makedirs(folder, exist_ok=True)
        
        # 파일명 생성 (URL의 마지막 부분 사용)
        filename = os.path.join(folder, os.path.basename(url.split('?')[0]))
        
        # User-Agent 헤더 추가
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36',
            'Referer': 'https://www.humorworld.net/'
        }
        
        # 최대 3번 재시도
        for attempt in range(3):
            try:
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()  # HTTP 에러 체크
                
                # 파일 저장
                with open(filename, 'wb') as f:
                    f.write(response.content)
                
                # 상대 경로 반환
                return os.path.relpath(filename, start='output/20250307')
                
            except requests.exceptions.RequestException as e:
                print(f"다운로드 실패 (시도 {attempt + 1}/3): {url}\n에러: {str(e)}")
                if attempt == 2:  # 마지막 시도였다면
                    return None
                time.sleep(2)  # 재시도 전 대기
                
    except Exception as e:
        print(f"미디어 다운로드 중 에러 발생: {str(e)}")
        return None

def infinite_scrape():
    print("\n=== HumorWorld 전체 게시글 스크래핑 시작 ===")
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument('--window-size=1920,1080')
    options.add_argument("--enable-unsafe-swiftshader")  # WebGL 오류 해결
    options.add_argument("--disable-software-rasterizer")  # 렌더링 오류 해결
    options.add_argument(f"user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36")
    
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        # 페이지 로드 타임아웃 설정
        driver.set_page_load_timeout(30)
        
        # 연결 재시도 횟수 설정
        max_retries = 3
        retry_delay = 5
        
        base_url = "https://www.humorworld.net/?cat=1&paged={}"
        page = 1
        total_posts = 0
        
        # 이전 게시물의 제목들을 저장할 집합
        previous_titles = set()
        output_dir = os.path.join('output', '20250307')
        
        # 이전 게시물 제목 로드
        if os.path.exists(os.path.join(output_dir, '1.html')):
            with open(os.path.join(output_dir, '1.html'), 'r', encoding='utf-8') as f:
                content = f.read()
                previous_titles = set(title.strip() for title in content.split('<h2>')[1:])
        
        while True:  # 무한 스크래핑
            for retry in range(max_retries):
                try:
                    current_url = base_url.format(page)
                    print(f"\n=== 페이지 {page} 스크래핑 중... (시도 {retry + 1}/{max_retries}) ===")
                    driver.get(current_url)
                    time.sleep(5)
                    break
                except Exception as e:
                    if retry == max_retries - 1:
                        raise e
                    print(f"페이지 로드 실패, {retry_delay}초 후 재시도...")
                    time.sleep(retry_delay)
            
            posts = driver.find_elements(By.CSS_SELECTOR, "article.post")
            if not posts:
                print(f"\n더 이상 게시글이 없습니다. 총 {total_posts}개의 게시글을 스크래핑했습니다.")
                break
                
            posts_data = []
            new_posts_count = 0
            media_folder = "downloaded_media"
            
            for post in posts:
                try:
                    title = post.find_element(By.CSS_SELECTOR, ".entry-title").text.strip()
                    
                    # 새 게시물인 경우에만 처리
                    if title not in previous_titles:
                        # 게시물 데이터 구조 수정
                        post_data = {
                            'title': title,
                            'content': post.find_element(By.CSS_SELECTOR, ".entry-content").text.strip(),
                            'images': [],
                            'videos': [],
                            'link': None
                        }
                        
                        # 미디어 다운로드 성공 여부 플래그
                        media_download_success = True
                        
                        # 이미지 처리
                        images = post.find_elements(By.CSS_SELECTOR, ".entry-content img")
                        for img in images:
                            img_url = img.get_attribute('src')
                            if img_url:
                                if not urlparse(img_url).netloc:
                                    img_url = f"https://www.humorworld.net{img_url}"
                                
                                saved_path = download_media(img_url, os.path.join(media_folder, 'images'))
                                if saved_path:
                                    post_data['images'].append(saved_path)
                                else:
                                    print(f"이미지 다운로드 실패로 게시물 건너뛰기: {title}")
                                    media_download_success = False
                                    break
                        
                        # 이미지 다운로드 실패시 다음 게시물로
                        if not media_download_success:
                            continue
                        
                        # 비디오 처리
                        videos = post.find_elements(By.CSS_SELECTOR, ".entry-content iframe[src*='youtube.com'], .entry-content iframe[src*='youtu.be'], .entry-content video")
                        for video in videos:
                            video_url = video.get_attribute('src')
                            if video_url:
                                if 'youtube.com' in video_url or 'youtu.be' in video_url:
                                    post_data['videos'].append(video_url)
                                elif video.tag_name == 'video':
                                    saved_path = download_media(video_url, os.path.join(media_folder, 'videos'))
                                    if saved_path:
                                        post_data['videos'].append(saved_path)
                                    else:
                                        print(f"비디오 다운로드 실패로 게시물 건너뛰기: {title}")
                                        media_download_success = False
                                        break
                        
                        # 비디오 다운로드 실패시 다음 게시물로
                        if not media_download_success:
                            continue
                        
                        # 모든 미디어가 성공적으로 다운로드된 경우에만 게시물 저장
                        posts_data.append(post_data)
                        new_posts_count += 1
                        total_posts += 1
                        print(f"제목: {post_data['title']}")
                        print(f"내용: {post_data['content'][:200]}...\n")
                        
                except Exception as e:
                    logging.error(f"게시글 파싱 중 오류: {str(e)}")
                    continue
            
            if posts_data:
                for post_data in posts_data:
                    save_to_html(post_data, page)
                    page += 1
                print(f"페이지 {page-1}: 새로운 게시글 {new_posts_count}개 저장됨")
                # 인덱스 파일 업데이트
                update_index_file(page-1)  # 여기서 인덱스가 업데이트됨
            
            if new_posts_count == 0:
                print(f"\n새로운 게시글이 없습니다. 총 {total_posts}개의 게시글을 스크래핑했습니다.")
                break
            
            # 사용자에게 계속할지 물어보기
            if page % 5 == 0:  # 5페이지마다
                try:
                    choice = input(f"\n현재 {total_posts}개의 게시글을 스크래핑했습니다. 계속하시겠습니까? (y/n): ")
                    if choice.lower() != 'y':
                        print(f"\n스크래핑을 종료합니다. 총 {total_posts}개의 게시글을 스크래핑했습니다.")
                        break
                except KeyboardInterrupt:
                    print("\n\n사용자가 중단했습니다. 지금까지의 결과를 저장합니다.")
                    break
                
    except Exception as e:
        print(f"에러 발생: {str(e)}")
    finally:
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    setup_logging()
    setup_database()
    infinite_scrape()
