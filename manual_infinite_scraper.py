import sys
import io
from scraping_example import (
    setup_logging, setup_database, save_post_to_db, 
    download_media, save_to_html, Options, webdriver, 
    Service, ChromeDriverManager, By, logging, time, os
)

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

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
                    post_data = {
                        'title': post.find_element(By.CSS_SELECTOR, ".entry-title").text.strip(),
                        'link': post.find_element(By.CSS_SELECTOR, ".entry-title a").get_attribute('href'),
                        'content': post.find_element(By.CSS_SELECTOR, ".entry-content").text.strip()[:200],
                        'images': [],
                        'videos': []
                    }
                    
                    if save_post_to_db(post_data):
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
                        print(f"링크: {post_data['link']}")
                        print(f"내용: {post_data['content']}...\n")
                        
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
