
BOT_NAME = "best_ranking_crawler"

SPIDER_MODULES = ["best_ranking_crawler.spiders"]
NEWSPIDER_MODULE = "best_ranking_crawler.spiders"

ROBOTSTXT_OBEY = True

# ─────── 로그 파일 ───────
# import os
# from datetime import datetime
# LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
# LOG_FILE = os.path.join(LOG_DIR, f"crawl_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log")
LOG_LEVEL = 'INFO'
# LOG_STDOUT = True

# ─────── DB ───────
MONGO_URI = 'mongodb://localhost:27017'
MONGO_DATABASE = 'amazon_reviews'
MONGO_COLLECTION = 'best_products'

REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

DOWNLOAD_HANDLERS = {
    'http': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
    'https': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
}

ITEM_PIPELINES = {
    'best_ranking_crawler.pipelines.CleanUnicodeCharsPipeline': 300,
    'best_ranking_crawler.pipelines.MongoPipeline': 350,
}

PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": False, 
    "slow_mo": 2000,
    "args": ["--no-sandbox", "--disable-dev-shm-usage"]
}

FEEDS = {
    './result/dbtest.json': {
        'format': 'json',
        'encoding': 'utf8',
        'indent': 4,
    }
}

USER_AGENT_CHOICES = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_2_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 12_6_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Fedora; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14526.83.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
]

DEFAULT_REQUEST_HEADERS = {
    'User-Agent': 'default-user-agent',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Upgrade-Insecure-Requests': '1',
    'Connection': 'keep-alive',
    "COOKIES_ENABLED": True
}
