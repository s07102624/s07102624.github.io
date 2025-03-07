import sys
import io
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

def save_html_file(page_num, html_content):
    output_dir = os.path.join('output', '20250307')
    os.makedirs(output_dir, exist_ok=True)
    
    # HTML 내용 변경
    html_content = replace_text_content(html_content)
    
    file_path = os.path.join(output_dir, f'{page_num}.html')
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

def save_to_html(posts_data, page_num):
    html_template = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <title>테스트프로 {page_num}페이지</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-9374368296307755" crossorigin="anonymous"></script>
        <style>
            body {{
                font-family: -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Oxygen-Sans,Ubuntu,Cantarell,"Helvetica Neue",sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                background: #f0f2f5;
            }}
            .content {{
                max-width: 1200px;
                margin: 0 auto;
                background: #fff;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 1px 2px rgba(0,0,0,0.1);
            }}
            .preview {{
                border-bottom: 1px solid #eee;
                padding: 20px 0;
            }}
            .preview h2 {{
                margin: 0 0 10px 0;
                font-size: 1.5em;
            }}
            .preview img, .preview video {{
                max-width: 100%;
                height: auto;
                margin: 10px 0;
                border-radius: 4px;
            }}
            .ad-container {{
                margin: 20px 0;
                text-align: center;
            }}
        </style>
    </head>
    <body>
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

    for post in posts_data:
        html_template += f"""
            <div class="preview">
                <h2>{post['title']}</h2>
                <div class="content">{post['content']}</div>
        """
        
        # 이미지 추가
        for img_path in post['images']:
            html_template += f'<img src="{img_path}" alt="이미지">\n'
            
        # 비디오 추가
        for video_path in post['videos']:
            html_template += f'<video controls src="{video_path}"></video>\n'
            
        html_template += "</div>\n"

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
    </body>
    </html>
    """

    save_html_file(page_num, html_template)

def infinite_scrape():
    print("\n=== HumorWorld 전체 게시글 스크래핑 시작 ===")
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument('--window-size=1920,1080')
    options.add_argument(f"user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36")
    
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        base_url = "https://www.humorworld.net/?cat=1&paged={}"
        page = 1
        total_posts = 0
        
        while True:  # 무한 스크래핑
            current_url = base_url.format(page)
            print(f"\n=== 페이지 {page} 스크래핑 중... ===")
            driver.get(current_url)
            time.sleep(5)
            
            posts = driver.find_elements(By.CSS_SELECTOR, "article.post")
            if not posts:
                print(f"\n더 이상 게시글이 없습니다. 총 {total_posts}개의 게시글을 스크래핑했습니다.")
                break
                
            posts_data = []
            new_posts_count = 0
            media_folder = "downloaded_media"
            
            for post in posts:
                try:
                    # 게시물 데이터 구조 수정
                    post_data = {
                        'title': post.find_element(By.CSS_SELECTOR, ".entry-title").text.strip(),
                        'content': post.find_element(By.CSS_SELECTOR, ".entry-content").text.strip(),
                        'images': [],
                        'videos': [],
                        'link': None  # link 키 추가
                    }
                    
                    new_posts_count += 1
                    total_posts += 1
                    
                    # 이미지와 비디오 처리
                    images = post.find_elements(By.CSS_SELECTOR, "img")
                    videos = post.find_elements(By.CSS_SELECTOR, "video source, iframe")
                    
                    for img in images:
                        img_url = img.get_attribute('src')
                        if img_url:
                            saved_path = download_media(img_url, os.path.join(media_folder, 'images'))
                            if saved_path:
                                post_data['images'].append(saved_path)
                    
                    for video in videos:
                        video_url = video.get_attribute('src')
                        if video_url:
                            saved_path = download_media(video_url, os.path.join(media_folder, 'videos'))
                            if saved_path:
                                post_data['videos'].append(saved_path)
                    
                    posts_data.append(post_data)
                    print(f"제목: {post_data['title']}")
                    print(f"내용: {post_data['content'][:200]}...\n")
                    
                except Exception as e:
                    logging.error(f"게시글 파싱 중 오류: {str(e)}")
                    continue
            
            if posts_data:
                save_to_html(posts_data, page)
                print(f"페이지 {page}: 새로운 게시글 {new_posts_count}개 저장됨")
            
            if new_posts_count == 0:
                print(f"\n새로운 게시글이 없습니다. 총 {total_posts}개의 게시글을 스크래핑했습니다.")
                break
                
            page += 1
            
            # 사용자에게 계속할지 물어보기
            if page % 5 == 0:  # 5페이지마다
                choice = input(f"\n현재 {total_posts}개의 게시글을 스크래핑했습니다. 계속하시겠습니까? (y/n): ")
                if choice.lower() != 'y':
                    print(f"\n스크래핑을 종료합니다. 총 {total_posts}개의 게시글을 스크래핑했습니다.")
                    break
                
    except Exception as e:
        print(f"에러 발생: {str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    setup_logging()
    setup_database()
    infinite_scrape()
