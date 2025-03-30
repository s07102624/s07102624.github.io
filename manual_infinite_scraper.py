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

def process_title(title):
    """제목에 랜덤 접두어와 접미어 추가"""
    prefix = random.choice(CLICK_PREFIXES)
    suffix = random.choice(INTEREST_SUFFIXES)
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
        if prev_post and 'title' in prev_post:
            prev_filename = clean_filename(process_title(prev_post['title'])) + '.html'
            nav_links.append(f'<a href="./{prev_filename}" style="color: #333; text-decoration: none; padding: 8px 15px; border-radius: 4px; transition: background-color 0.3s;">◀ 이전 글</a>')
        
        nav_links.append('<a href="https://kk.testpro.site/" style="color: #333; text-decoration: none; padding: 8px 15px; border-radius: 4px; background-color: #f0f0f0; transition: background-color 0.3s;">홈</a>')
        
        if next_post and 'title' in next_post:
            next_filename = clean_filename(process_title(next_post['title'])) + '.html'
            nav_links.append(f'<a href="./{next_filename}" style="color: #333; text-decoration: none; padding: 8px 15px; border-radius: 4px; transition: background-color 0.3s;">다음 글 ▶</a>')
        
        nav_html = '\n'.join(nav_links)

        # content가 BeautifulSoup 객체인 경우 HTML 추출
        if isinstance(content, BeautifulSoup):
            # 제목을 본문 시작 부분에 추가
            title_html = f'<h2 style="font-size: 1.5em; margin-bottom: 20px; color: #333; font-weight: bold;">{processed_title}</h2>'
            content_html = str(content)
            content_html = title_html + content_html
            content_html = content_html.replace('src="/', 'src="https://humorworld.net/')
        else:
            content_html = f"<h2>{processed_title}</h2><p>{content}</p>"

        html_content = f"""<!DOCTYPE html>
<html lang="ko-KR" class="js">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{processed_title}</title>
    
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
            display: flex;
            justify-content: center;
            min-height: 100vh;
        }}
        
        /* 컨테이너 레이아웃 */
        .container {{
            width: 100%;
            max-width: 1200px;
            margin: 20px auto;
            padding: 0 20px;
            display: flex;
            justify-content: center;
            align-items: flex-start;
            gap: 30px;
        }}
        
        /* 메인 콘텐츠 영역 */
        .content-area {{
            width: 800px;
            background: #fff;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            padding: 30px;
            margin: 0 auto;
        }}
        
        /* 사이드바 제거하고 메인 컨텐츠 중앙 정렬 */
        .widget-area {{
            display: none;
        }}
        
        /* 광고 컨테이너 중앙 정렬 */
        .ad-container {{
            width: 100%;
            max-width: 728px;
            margin: 20px auto;
            text-align: center;
        }}
        
        /* 반응형 디자인 */
        @media (max-width: 768px) {{
            .container {{
                padding: 10px;
            }}
            
            .content-area {{
                width: 100%;
                padding: 15px;
            }}
        }}

        /* 하단 네비게이션 중앙 정렬 */
        .bottom-navigation .container {{
            padding: 0;
            margin: 0 auto;
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
                        <div class="nav-links">
                            {f'<div class="nav-previous"><a href="{prev_post["filename"]}">{prev_post["title"]}</a></div>' if prev_post else ''}
                            {f'<div class="nav-next"><a href="{next_post["filename"]}">{next_post["title"]}</a></div>' if next_post else ''}
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

def scrape_category():
    """게시물 스크래핑 함수"""
    base_path, image_path = setup_folders()
    posts_info = []  # 모든 게시물 정보를 저장할 리스트
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

                    # 현재 게시물 정보 저장 - 구조 수정
                    current_post = {
                        'title': title,
                        'content': content,
                        'images': images_html,
                        'filename': f'{clean_filename(process_title(title))}.html'  # filename 추가
                    }
                    
                    # 이전/다음 게시물 정보 설정
                    prev_post = posts_info[-1] if posts_info else None
                    
                    # 게시물 저장
                    saved_file = save_article(
                        title,
                        content,  # BeautifulSoup 객체 그대로 전달
                        images_html,
                        base_path,
                        prev_post,
                        None  # 다음 게시물은 아직 알 수 없음
                    )
                    
                    # 게시물 정보 저장
                    if saved_file:
                        posts_info.append(current_post)
                        
                        # 이전 게시물 업데이트
                        if prev_post:
                            save_article(
                                prev_post['title'],
                                prev_post['content'],
                                prev_post['images'],
                                base_path,
                                posts_info[-3] if len(posts_info) > 2 else None,
                                current_post
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
