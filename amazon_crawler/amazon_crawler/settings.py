BOT_NAME = 'amazon_crawler'

SPIDER_MODULES = ['amazon_crawler.spiders']
NEWSPIDER_MODULE = 'amazon_crawler.spiders'

# ─────── 출력 ───────
FEED_EXPORT_ENCODING = 'utf-8'
FEEDS = {
    './data/result/데이터 적재/원본/8001.json': {
        'format': 'json',
        'encoding': 'utf8',
        'indent': 4,
    }
}

# ─────── 요청/응답 ───────
DOWNLOAD_TIMEOUT = 30
DOWNLOAD_DELAY = 2
RANDOMIZE_DOWNLOAD_DELAY = True  #True였음
CONCURRENT_REQUESTS = 8
CONCURRENT_REQUESTS_PER_DOMAIN = 1

COOKIES_ENABLED = True
HTTPCACHE_ENABLED = False

# ─────── 로그 파일 ───────
import os
from datetime import datetime
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
LOG_FILE = os.path.join(LOG_DIR, f"crawl_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log")
LOG_LEVEL = 'DEBUG'
LOG_STDOUT = True

# ─────── User-Agent 목록 … (생략) ───────
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

# ─────── 재시도 / 미들웨어 ───────
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 403, 429]

DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,
    'amazon_crawler.middlewares.CustomRetryMiddleware': 550,
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'amazon_crawler.middlewares.RandomUserAgentMiddleware': 400,
    # 'amazon_crawler.middlewares.CustomProxyMiddleware': 350,
    'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
    # ❶ Playwright 자체 미들웨어는 **자동**으로 주입되므로 추가 필요 없음
}

# ─────── 프록시 / 파이프라인 / Referer 등 기존 설정 유지 ───────
PROXIES = [
    '14a22fccc4885:a48fd5bd91@45.150.81.133:12323',
    '14a22fccc4885:a48fd5bd91@89.47.126.25:12323',
    '14a22fccc4885:a48fd5bd91@139.171.28.145:12323',
    '14a22fccc4885:a48fd5bd91@104.234.9.235:12323',
    '14a22fccc4885:a48fd5bd91@88.209.232.21:12323',
    '14a22fccc4885:a48fd5bd91@92.112.8.87:12323',
    '14a22fccc4885:a48fd5bd91@198.143.20.64:12323',
    '14a22fccc4885:a48fd5bd91@130.255.64.223:12323',
    '14a22fccc4885:a48fd5bd91@149.18.82.184:12323',
    '14a22fccc4885:a48fd5bd91@77.111.123.77:12323'
]
PROXY_RECOVERY_TIME = 1800  # 30 분

# ─────── 파이프라인 설정 ───────
ITEM_PIPELINES = {
    'amazon_crawler.pipelines.CleanUnicodeCharsPipeline': 300,
}
# ─────── Referer 설정 ───────
REFERER_ENABLED = True
REFERRER_POLICY = 'scrapy.spidermiddlewares.referer.DefaultReferrerPolicy'

# ─────── 기본 헤더 설정 ───────
DEFAULT_REQUEST_HEADERS = {
    'User-Agent': 'default-user-agent',
    # 'Referer': 'https://www.amazon.com/s?k=internal+hard+drive',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Upgrade-Insecure-Requests': '1',
    'Connection': 'keep-alive',
    "COOKIES_ENABLED": True
}
# ────────────────────────────────────────────────────────────────
