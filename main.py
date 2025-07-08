import subprocess

# 제품 정보 크롤러 실행 
subprocess.run([
    "scrapy", "crawl", "amazon_product",
], cwd='./crawling/amazon_crawler/')

# 베스트 셀러 크롤러 실행
subprocess.run([
    "scrapy", "crawl", "best",
], cwd='./crawling/best_ranking_crawler/')

# 리뷰 크롤러 실행
subprocess.run([
    "python", "main.py",
    "--login_browser", "firefox",
    "--login_headless",
    "--crawling_headless",
    "--use_proxy",
    "--asin_start", "0",
    "--asin_end", "10",
    "--max_pages", "2",
    "--max_concurrent_contexts", "5",
    "--log_level", "DEBUG"
], cwd='./review/amazon_crawl/amazon_reviews/crawler/v1')
