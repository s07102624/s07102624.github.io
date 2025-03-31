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
    from PIL import Image
    import io
except ImportError as e:
    print(f"필요한 패키지가 설치되지 않았습니다: {str(e)}")
    print("다음 명령어로 필요한 패키지를 설치하세요:")
    print("pip install beautifulsoup4 cloudscraper fake-useragent pillow")
    sys.exit(1)

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 클릭 유도 접두어와 흥미로운 주제 접미어 리스트 추가
CLICK_PREFIXES = [
    "충격", "경악", "화제", "논란", "실화", "대박", "궁금", "알고보니", "충격적", "결국",
    "현실", "경악", "공감", "화제의", "완벽", "역대급", "필독", "최초", "극과극", "충격반전",
    "실시간", "속보", "단독", "전격", "긴급", "초특급", "절대", "화제의", "놀라운", "충격적인",
    "완전", "초강력", "강추", "필수", "대유행", "최강", "극한", "전설의", "상상초월", "신기한"
]

INTEREST_SUFFIXES = [
    "비하인드", "꿀팁", "레전드", "사연", "현실", "반전", "근황", "비밀", "이야기", "심쿵",
    "순간", "기적", "노하우", "핵심", "비결", "대반전", "진실", "TMI", "모음", "영상",
    "현장", "총정리", "요약", "정보", "모음집", "기록", "사실", "모먼트", "포인트", "궁금증",
    "꿀잼", "분석", "해설", "후기", "리뷰", "정리", "모음", "꿀팁", "레시피", "노하우"
]

def clean_filename(text):
    """파일명으로 사용할 수 있게 문자열 정리"""
    # 기본 파일명 정리
    cleaned = re.sub(r'[\\/*?:"<>|]', "", text)
    # URL에서 사용할 수 있도록 추가 처리
    cleaned = cleaned.replace(' ', '-')  # 공백을 하이픈으로 변경
    cleaned = re.sub(r'[^\w\-\.]', '', cleaned)  # 알파벳, 숫자, 하이픈, 점만 허용
    cleaned = re.sub(r'-+', '-', cleaned)  # 연속된 하이픈을 하나로
    return cleaned.strip('-')  # 앞뒤 하이픈 제거

def process_title(title, prefix_index=None, suffix_index=None):
    """제목에 일관된 접두어와 접미어 추가"""
    # seed를 사용하여 일관된 접두어/접미어 선택
    if prefix_index is None:
        # 제목을 기반으로 일관된 인덱스 생성
        prefix_index = hash(title) % len(CLICK_PREFIXES)
    if suffix_index is None:
        suffix_index = hash(title + "suffix") % len(INTEREST_SUFFIXES)
        
    prefix = CLICK_PREFIXES[prefix_index]
    suffix = INTEREST_SUFFIXES[suffix_index]
    return f"[{prefix}] {title} ({suffix})"

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
        # 제목 처리
        processed_title = process_title(title)
        safe_title = clean_filename(processed_title)
        filename = os.path.join(base_path, f'{safe_title}.html')
        
        # 네비게이션 링크 설정 - 파일명 처리 수정
        nav_links = []
        if prev_post and 'filename' in prev_post:
            nav_links.append(f'<a href="./{prev_post["filename"]}" style="color: #333; text-decoration: none; padding: 8px 15px; border-radius: 4px; transition: background-color 0.3s;">◀ 이전 글</a>')
        
        # 홈 링크를 humor_1.html로 변경
        nav_links.append('<a href="./humor_1.html" style="color: #333; text-decoration: none; padding: 8px 15px; border-radius: 4px; background-color: #f0f0f0; transition: background-color 0.3s;">홈</a>')
        
        if next_post and 'filename' in next_post:
            nav_links.append(f'<a href="./{next_post["filename"]}" style="color: #333; text-decoration: none; padding: 8px 15px; border-radius: 4px; transition: background-color 0.3s;">다음 글 ▶</a>')
        
        nav_html = '\n'.join(nav_links)

        # content가 BeautifulSoup 객체인 경우 HTML 추출
        if isinstance(content, BeautifulSoup):
            content_html = str(content)
            # 원본 HTML 구조 유지를 위해 태그 보존
            content_html = content_html.replace('src="/', 'src="https://humorworld.net/')
        else:
            content_html = f"<p>{content}</p>"

        html_content = f"""<!DOCTYPE html>
<html lang="ko-KR" class="js">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="robots" content="noindex, nofollow">
    
    <!-- 네이버 밴드 썸네일 비활성화 -->
    <meta property="og:type" content="website">
    <meta property="og:title" content="{processed_title}">
    <meta property="og:description" content="">
    <meta property="og:image" content="">
    <meta property="og:url" content="">
    <meta name="twitter:card" content="none">
    <link rel="image_src" href="">
    
    <title>{processed_title}</title>
    
    <!-- 검색엔진 노출 제한 -->
    <meta name="googlebot" content="noindex,nofollow">
    <meta name="googlebot-news" content="nosnippet">
    <meta name="robots" content="noarchive">
    
    <!-- 원본 스타일시트 -->
    <link rel='stylesheet' id='wp-block-library-css' href='https://humorworld.net/wp-includes/css/dist/block-library/style.min.css' type='text/css' media='all' />
    <link rel='stylesheet' id='classic-theme-styles-css' href='https://humorworld.net/wp-includes/css/classic-themes.min.css' type='text/css' media='all' />
    <link rel='stylesheet' id='blogberg-style-css' href='https://humorworld.net/wp-content/themes/blogberg/style.css' type='text/css' media='all' />
    <link rel='stylesheet' id='blogberg-google-fonts-css' href='https://fonts.googleapis.com/css?family=Poppins:300,400,400i,500,600,700,700i|Rubik:300,400,400i,500,700,700i' type='text/css' media='all' />
    <link rel='stylesheet' id='bootstrap-css' href='https://humorworld.net/wp-content/themes/blogberg/assets/vendors/bootstrap/css/bootstrap.min.css' type='text/css' media='all' />
    
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-9374368296307755" crossorigin="anonymous"></script>
    
    <style type="text/css">
        /* 기본 스타일 */
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Noto Sans KR", "Segoe UI", Roboto, Oxygen-Sans, Ubuntu, Cantarell, "Helvetica Neue", sans-serif;
            line-height: 1.8;
            color: #333333;
            background-color: #f8f9fa;
            margin: 0;
            padding: 0;
            min-height: 100vh;
            width: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        
        /* 컨테이너 레이아웃 */
        .container {{
            width: 100%;
            max-width: 1200px;
            margin: 20px auto;
            padding: 0 15px;
            box-sizing: border-box;
        }}
        
        /* 메인 콘텐츠 영역 */
        .content-area {{
            width: 100%;
            max-width: 800px;
            background: #fff;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            padding: 20px;
            margin: 0 auto;
            box-sizing: border-box;
        }}
        
        /* 이미지 반응형 처리 */
        .entry-content img {{
            max-width: 100%;
            height: auto;
            display: block;
            margin: 0 auto;
        }}
        
        /* 광고 컨테이너 중앙 정렬 */
        .ad-container {{
            width: 100%;
            max-width: 728px;
            margin: 20px auto;
            text-align: center;
            overflow: hidden;
        }}
        
        /* 반응형 디자인 */
        @media (max-width: 768px) {{
            body {{
                padding: 0;
            }}
            
            .container {{
                padding: 10px;
                margin: 10px auto;
            }}
            
            .content-area {{
                padding: 15px;
                border-radius: 0;
            }}
            
            .entry-title {{
                font-size: 1.5em;
                word-break: keep-all;
            }}
            
            .bottom-navigation .container {{
                padding: 0 10px;
            }}
            
            .nav-links {{
                font-size: 0.9em;
            }}
        }}

        /* 하단 네비게이션 중앙 정렬 */
        .bottom-navigation .container {{
            padding: 0;
            margin: 0 auto;
            width: 100%;
        }}
        
        .nav-links {{
            justify-content: center;
            gap: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <main class="content-area">
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
            
            <article class="post">
                <header class="entry-header">
                    <h1 class="entry-title">{processed_title}</h1>
                    <div class="entry-meta">
                        <span class="posted-on">
                            <time class="entry-date published">{datetime.now().strftime('%Y년 %m월 %d일')}</time>
                        </span>
                    </div>
                </header>
                <div class="entry-content">
                    {content_html}
                    {images}
                </div>
                <footer class="entry-footer">
                    <nav class="navigation post-navigation">
                        <div class="nav-links" style="display: flex; justify-content: space-between; margin: 20px 0;">
                            {f'<div class="nav-previous"><a href="./{prev_post["filename"]}">{prev_post["title"]}</a></div>' if prev_post else ''}
                            {f'<div class="nav-next"><a href="./{next_post["filename"]}">{next_post["title"]}</a></div>' if next_post else ''}
                        </div>
                    </nav>
                </footer>
            </article>
            
            <!-- 하단 광고 -->
            <div class="ad-container">
                <ins class="adsbygoogle"
                     style="display:block"
                     data-ad-client="ca-pub-9374368296307755"
                     data-ad-slot="8384240134"
                     data-ad-format="auto"
                     data-full-width-responsive="true"></ins>
                <script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>
            </div>
        </main>
    </div>
    
    <!-- 고정 광고 -->
    <div class="ad-fixed">
        <ins class="adsbygoogle"
             style="display:inline-block;width:300px;height:250px"
             data-ad-client="ca-pub-9374368296307755"
             data-ad-slot="8384240134"></ins>
        <script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>
    </div>
    
    <!-- 하단 네비게이션 바 추가 -->
    <nav class="bottom-navigation" style="
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: #fff;
        box-shadow: 0 -2px 5px rgba(0,0,0,0.1);
        padding: 10px 0;
        z-index: 1000;
    ">
        <div class="container">
            <div class="nav-links" style="
                display: flex;
                justify-content: space-between;
                align-items: center;
                max-width: 600px;
                margin: 0 auto;
                padding: 0 20px;
            ">
                {nav_html}
            </div>
        </div>
    </nav>
    
    <div style="height: 60px;"><!-- 하단 네비게이션 바 공간 확보 --></div>
    
    <!-- 원본 사이트 스크립트 -->
    <script src='https://humorworld.net/wp-includes/js/jquery/jquery.min.js' id='jquery-core-js'></script>
    <script src='https://humorworld.net/wp-content/themes/blogberg/assets/vendors/bootstrap/js/bootstrap.min.js' id='bootstrap-js'></script>
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
    """게시물 제목 중복 검사 - 처리된 제목 사용"""
    processed_title = process_title(title)
    safe_title = clean_filename(processed_title)
    return os.path.exists(os.path.join(base_path, f'{safe_title}.html'))

def create_humor_page(posts_info, base_path, page_number=1):
    """유머 페이지 생성"""
    posts_per_page = 10
    total_posts = len(posts_info)
    total_pages = (total_posts + posts_per_page - 1) // posts_per_page
    
    # 현재 페이지의 게시물 계산
    start_idx = (page_number - 1) * posts_per_page
    end_idx = min(start_idx + posts_per_page, total_posts)
    current_posts = posts_info[start_idx:end_idx]
    
    # 네비게이션 링크 추가
    nav_links = []
    if page_number > 1:
        nav_links.append(f'<a href="./humor_{page_number-1}.html" style="color: #333; text-decoration: none; padding: 8px 15px; border-radius: 4px; transition: background-color 0.3s;">◀ 이전</a>')
    
    nav_links.append(f'<span style="color: #333; padding: 8px 15px;">페이지 {page_number}</span>')
    
    if page_number < total_pages:
        nav_links.append(f'<a href="./humor_{page_number+1}.html" style="color: #333; text-decoration: none; padding: 8px 15px; border-radius: 4px; transition: background-color 0.3s;">다음 ▶</a>')
    
    nav_html = '\n'.join(nav_links)
    
    # 페이지네이션 HTML 수정 - 이전/다음 페이지 버튼 추가
    pagination_html = '<div class="pagination" style="margin-top: 20px; text-align: center;">'
    
    # 이전 페이지 링크
    if page_number > 1:
        pagination_html += f'<a href="./humor_{page_number-1}.html" style="margin: 0 5px; padding: 5px 10px; text-decoration: none; color: #333;">◀</a>'
    
    # 페이지 번호
    for i in range(1, total_pages + 1):
        if i == page_number:
            pagination_html += f'<span style="margin: 0 5px; padding: 5px 10px; background-color: #f0f0f0; border-radius: 3px;">{i}</span>'
        else:
            pagination_html += f'<a href="./humor_{i}.html" style="margin: 0 5px; padding: 5px 10px; text-decoration: none; color: #333;">{i}</a>'
    
    # 다음 페이지 링크
    if page_number < total_pages:
        pagination_html += f'<a href="./humor_{page_number+1}.html" style="margin: 0 5px; padding: 5px 10px; text-decoration: none; color: #333;">▶</a>'
    
    pagination_html += '</div>'

    # 게시물 목록 HTML 생성 수정
    posts_html = '<ul style="list-style: none; padding: 0;">'
    for post in current_posts:
        posts_html += f'''
        <li style="margin: 15px 0; padding: 15px; background-color: #fff; border-radius: 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <a href="./{post['filename']}" style="text-decoration: none; color: #333; display: block;">
                <h2 style="margin: 0; font-size: 18px;">{post['title']}</h2>
            </a>
        </li>'''
    posts_html += '</ul>'

    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>유머 게시판 - 페이지 {page_number}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Noto Sans KR", sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1 {{
            text-align: center;
            margin-bottom: 30px;
            color: #333;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>유머 게시판</h1>
        {posts_html}
        {pagination_html}
    </div>
    
    <!-- 하단 네비게이션 바 추가 -->
    <nav class="bottom-navigation" style="
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: #fff;
        box-shadow: 0 -2px 5px rgba(0,0,0,0.1);
        padding: 10px 0;
        z-index: 1000;
    ">
        <div class="container">
            <div class="nav-links" style="
                display: flex;
                justify-content: space-between;
                align-items: center;
                max-width: 600px;
                margin: 0 auto;
                padding: 0 20px;
            ">
                {nav_html}
            </div>
        </div>
    </nav>
    
    <div style="height: 60px;"><!-- 하단 네비게이션 바 공간 확보 --></div>
</body>
</html>"""

    filename = f'humor_{page_number}.html'
    with open(os.path.join(base_path, filename), 'w', encoding='utf-8') as f:
        f.write(html_content)

def update_humor_pages(posts_info, base_path):
    """모든 유머 페이지 업데이트"""
    total_posts = len(posts_info)
    total_pages = (total_posts + 9) // 10  # 10개씩 표시

    for page in range(1, total_pages + 1):
        create_humor_page(posts_info, base_path, page)

def initialize_humor_page(base_path):
    """초기 유머 페이지 생성"""
    # 초기 페이지를 humor_1.html로 생성
    html_content = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>유머 게시판</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Noto Sans KR", sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f8f9fa;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 {
            text-align: center;
            margin-bottom: 30px;
            color: #333;
        }
        #post-list {
            list-style: none;
            padding: 0;
        }
        .pagination {
            margin-top: 20px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>유머 게시판</h1>
        <ul id="post-list"></ul>
        <div class="pagination"></div>
    </div>
</body>
</html>"""
    
    with open(os.path.join(base_path, 'humor_1.html'), 'w', encoding='utf-8') as f:
        f.write(html_content)

def scrape_category():
    """게시물 스크래핑 함수"""
    base_path, image_path = setup_folders()
    posts_info = []
    
    # 초기 유머 페이지 생성
    initialize_humor_page(base_path)
    
    try:
        scraper = get_scraper()
        page = 1
        
        while True:
            base_url = 'https://humorworld.net/category/humorstorage/'
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
                    
                    # 제목의 해시값을 사용하여 일관된 접두어/접미어 선택
                    prefix_index = hash(title) % len(CLICK_PREFIXES)
                    suffix_index = hash(title + "suffix") % len(INTEREST_SUFFIXES)
                    processed_title = process_title(title, prefix_index, suffix_index)
                    safe_filename = clean_filename(processed_title) + '.html'
                    
                    # 중복 게시물 검사 - processed_title 사용
                    if os.path.exists(os.path.join(base_path, safe_filename)):
                        logging.info(f"Skipping duplicate post: {title}")
                        continue
                    
                    # 게시물 정보를 딕셔너리에 저장
                    current_post = {
                        'title': title,
                        'processed_title': processed_title,
                        'filename': safe_filename,
                        'prefix_index': prefix_index,
                        'suffix_index': suffix_index,
                        'content': None,
                        'images': None,
                        'page_number': (len(posts_info) // 10) + 1  # 페이지 번호 추가
                    }
                    
                    # 게시물 상세 페이지 스크래핑
                    article_response = scraper.get(link)
                    article_soup = BeautifulSoup(article_response.text, 'html.parser')
                    
                    content = article_soup.select_one('.entry-content')
                    if not content:
                        logging.error(f"Content not found for: {title}")
                        continue

                    # 이미지 처리 - WebP 변환 추가
                    images_html = ""
                    for img in content.find_all('img'):
                        if img.get('src'):
                            img_name = clean_filename(os.path.basename(img['src']))
                            webp_name = f"{os.path.splitext(img_name)[0]}.webp"
                            img_path = os.path.join(image_path, webp_name)
                            
                            try:
                                # 이미지 다운로드
                                img_response = scraper.get(img['src'])
                                img_data = Image.open(io.BytesIO(img_response.content))
                                
                                # RGBA 이미지를 RGB로 변환
                                if img_data.mode in ('RGBA', 'LA'):
                                    background = Image.new('RGB', img_data.size, (255, 255, 255))
                                    background.paste(img_data, mask=img_data.split()[-1])
                                    img_data = background
                                
                                # WebP로 저장 (품질 85%)
                                img_data.save(img_path, 'WEBP', quality=85)
                                images_html += f'<img src="images/{webp_name}" alt="{title}" loading="lazy">\n'
                                logging.info(f"Image saved as WebP: {webp_name}")
                            except Exception as e:
                                logging.error(f"Failed to process image: {str(e)}")

                    # 이전/다음 게시물 설정
                    prev_post = None
                    next_post = None
                    
                    # 현재 게시물의 페이지 번호와 인덱스 계산
                    current_page = (len(posts_info)) // 10 + 1
                    current_index = (len(posts_info)) % 10
                    
                    # 첫 페이지 첫 글이 아닌 경우 이전 글 설정
                    if len(posts_info) > 0:
                        prev_post = posts_info[-1]
                    
                    # 다음 게시물 설정
                    if len(posts_info) > 1:
                        # 페이지의 마지막 글이 아닌 경우
                        if current_index < 9:
                            next_post = posts_info[-2]
                    
                    # 현재 게시물 저장
                    saved_file = save_article(
                        current_post['title'],
                        content,
                        images_html,
                        base_path,
                        prev_post,  # 이전 게시물
                        next_post   # 다음 게시물
                    )
                    
                    if saved_file:
                        # 이전 게시물이 있는 경우 해당 게시물의 다음 글로 현재 게시물 설정
                        if prev_post:
                            save_article(
                                prev_post['title'],
                                content if 'content' in prev_post else None,
                                prev_post.get('images', ''),
                                base_path,
                                posts_info[-2] if len(posts_info) > 1 else None,  # 이전 글의 이전 글
                                current_post  # 현재 게시물을 다음 글로 설정
                            )
                        
                        posts_info.append(current_post)

                    time.sleep(random.uniform(2, 4))
                    
                except Exception as e:
                    logging.error(f'Error processing article: {str(e)}')
                    continue
            
            # 페이지 단위로 유머 페이지 업데이트
            update_humor_pages(posts_info, base_path)
            
            page += 1
            time.sleep(random.uniform(3, 5))
            
    except Exception as e:
        logging.error(f'Error occurred: {str(e)}')
    finally:
        # humor.html을 humor_1.html로 리다이렉트하는 파일 생성
        redirect_html = """<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="0;url=humor_1.html">
</head>
<body>
    <script>window.location.href = 'humor_1.html';</script>
</body>
</html>"""
        with open(os.path.join(base_path, 'humor.html'), 'w', encoding='utf-8') as f:
            f.write(redirect_html)
            
        # 최종 유머 페이지 업데이트
        update_humor_pages(posts_info, base_path)

if __name__ == '__main__':
    print('Starting to scrape humorworld.net category...')
    scrape_category()
    print('Scraping completed!')
