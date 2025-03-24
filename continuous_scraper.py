import sys
import io
from datetime import datetime  # datetime import 추가
from scraping_example import (
    setup_logging, setup_database, save_post_to_db, 
    download_media, save_to_html, Options, webdriver, 
    Service, ChromeDriverManager, By, logging, time, os
)
import hashlib

def get_next_file_number(output_dir):
    """다음 HTML 파일 번호를 찾습니다 (기존 번호 중 가장 큰 수 + 1)"""
    existing_files = [f for f in os.listdir(output_dir) if f.endswith('.html')]
    if not existing_files:
        return 101  # 시작 번호
    
    max_num = max(int(f.split('.')[0]) for f in existing_files if f.split('.')[0].isdigit())
    return max_num + 1

def is_post_exists(post_hash, base_path):
    """해시값을 이용해 게시물 중복 검사"""
    hash_file = os.path.join(base_path, 'post_hashes.txt')
    
    # 해시 파일이 없으면 생성
    if not os.path.exists(hash_file):
        return False
        
    # 해시 파일에서 기존 해시값들을 읽어옴
    with open(hash_file, 'r', encoding='utf-8') as f:
        existing_hashes = f.read().splitlines()
    
    return post_hash in existing_hashes

def save_post_hash(post_hash, base_path):
    """게시물 해시값 저장"""
    hash_file = os.path.join(base_path, 'post_hashes.txt')
    with open(hash_file, 'a', encoding='utf-8') as f:
        f.write(f"{post_hash}\n")

def process_single_page(driver, page, output_dir):
    """한 페이지를 스크랩하고 새로운 게시글만 HTML 생성"""
    print(f"\n=== 페이지 {page}/100 처리 시작 ===")
    
    # 1. 페이지 로드
    current_url = f"https://www.humorworld.net/?paged={page}"
    print(f"URL 로드 중: {current_url}")
    driver.get(current_url)
    time.sleep(3)
    
    # 2. 게시글 수집
    posts = driver.find_elements(By.CSS_SELECTOR, "article.post")
    if not posts:
        print(f"페이지 {page}에서 게시글을 찾을 수 없습니다.")
        return 0
    
    # 3. 게시글 처리
    posts_data = []
    for post in posts:
        try:
            post_data = {
                'title': post.find_element(By.CSS_SELECTOR, ".entry-title").text.strip(),
                'link': post.find_element(By.CSS_SELECTOR, ".entry-title a").get_attribute('href'),
                'content': post.find_element(By.CSS_SELECTOR, ".entry-content").text.strip(),
                'images': [],
                'videos': []
            }
            
            # 이미지/비디오 수집
            images = post.find_elements(By.CSS_SELECTOR, "img")
            videos = post.find_elements(By.CSS_SELECTOR, "video source, iframe")
            
            for img in images:
                if url := img.get_attribute('src'):
                    post_data['images'].append(url)
            
            for video in videos:
                if url := video.get_attribute('src'):
                    post_data['videos'].append(url)
            
            posts_data.append(post_data)
            print(f"게시글 추가: {post_data['title']}")
            
        except Exception as e:
            print(f"게시글 처리 중 오류: {str(e)}")
            continue
    
    # 4. 새로운 게시글만 HTML 파일 생성
    if posts_data:
        new_posts = []
        for post in posts_data:
            # 중복 체크
            post_id = hashlib.md5(post['link'].encode()).hexdigest()
            if not is_post_exists(post_id, output_dir):
                new_posts.append(post)
                save_post_to_db(post)
                save_post_hash(post_id, output_dir)
        
        if new_posts:
            file_number = get_next_file_number(output_dir)
            html_file = os.path.join(output_dir, f"{file_number}.html")
            print(f"\n새로운 게시글 발견! HTML 파일 생성 중... (파일번호: {file_number})")
            
            with open(html_file, 'w', encoding='utf-8') as f:
                html_content = [
                    '<!DOCTYPE html>',
                    '<html lang="ko">',
                    '<head>',
                    '    <meta charset="UTF-8">',
                    f'    <title>유머월드 {page}페이지</title>',
                    '    <meta name="viewport" content="width=device-width, initial-scale=1">',
                    '    <link rel="stylesheet" href="styles.css">',
                    '    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-9374368296307755" crossorigin="anonymous"></script>',
                    '</head>',
                    '<body>',
                    '    <div class="content">',
                    f'        <h1>유머월드 - 페이지 {page}</h1>',
                    '',
                    '        <!-- 상단 광고 -->',
                    '        <div class="ad-container">',
                    '            <ins class="adsbygoogle"',
                    '                 style="display:block"',
                    '                 data-ad-client="ca-pub-9374368296307755"',
                    '                 data-ad-slot="8384240134"',
                    '                 data-ad-format="auto"',
                    '                 data-full-width-responsive="true"></ins>',
                    '            <script>(adsbygoogle = window.adsbygoogle || []).push({});</script>',
                    '        </div>'
                ]
                
                for post in new_posts:
                    html_content.extend([
                        '        <div class="preview">',
                        f'            <h2><a href="{post["link"]}" target="_blank">{post["title"]}</a></h2>',
                        f'            <div class="content">{post["content"]}</div>'
                    ])
                    
                    for img in post['images']:
                        html_content.append(f'            <img src="{img}" alt="이미지">')
                    
                    for video in post['videos']:
                        html_content.append(f'            <video controls src="{video}"></video>')
                    
                    html_content.append('        </div>')
                
                html_content.extend([
                    '        <!-- 하단 광고 -->',
                    '        <div class="ad-container">',
                    '            <ins class="adsbygoogle"',
                    '                 style="display:block"',
                    '                 data-ad-client="ca-pub-9374368296307755"',
                    '                 data-ad-slot="8384240134"',
                    '                 data-ad-format="auto"',
                    '                 data-full-width-responsive="true"></ins>',
                    '            <script>(adsbygoogle = window.adsbygoogle || []).push({});</script>',
                    '        </div>',
                    '    </div>',
                    '</body>',
                    '</html>'
                ])
                
                f.write('\n'.join(html_content))
            
            print(f"HTML 생성 완료: {html_file} (새 게시글 수: {len(new_posts)}개)")
            return len(new_posts)
        else:
            print("새로운 게시글이 없습니다.")
            return 0
    
    return 0

def scrape_continuously():
    print("\n=== HumorWorld 스크래핑 시작 (새 파일은 101번부터) ===")
    
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument('--window-size=1920,1080')
    options.add_argument(f"user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36")
    
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        output_dir = os.path.join("output", datetime.now().strftime("%Y%m%d"))
        os.makedirs(output_dir, exist_ok=True)
        
        total_posts = 0
        for page in range(1, 101):  # 1부터 100까지
            try:
                posts_count = process_single_page(driver, page, output_dir)
                total_posts += posts_count
                
                print(f"\n=== 페이지 {page} 완료 (새 게시글: {posts_count}개, 총: {total_posts}개) ===\n")
                time.sleep(2)  # 다음 페이지 처리 전 대기
                
            except Exception as e:
                print(f"페이지 {page} 처리 중 오류 발생: {str(e)}")
                print("10초 후 다음 페이지로 진행...")
                time.sleep(10)
                continue
        
        print(f"\n=== 전체 스크래핑 완료! 총 {total_posts}개의 게시글 처리됨 ===")
        
    except Exception as e:
        print(f"스크래퍼 오류: {str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    setup_logging()
    setup_database()
    
    try:
        scrape_continuously()
    except KeyboardInterrupt:
        print("\n사용자가 프로그램을 중단했습니다.")
    except Exception as e:
        print(f"치명적인 오류 발생: {str(e)}")