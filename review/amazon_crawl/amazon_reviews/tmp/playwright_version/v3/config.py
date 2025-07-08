"""
로그인 및 환경설정 관련 설정 파일
각 selector/indicator 변수별로 어떤 단계에서 어떤 역할을 하는지 상세 주석 포함
여러 계정 지원: .env에서 계정별로 이메일,비번을 묶어서 리스트로 관리하고, 실행 시 랜덤으로 계정 1쌍을 선택
"""
import os
import random
from dotenv import load_dotenv
import platform
import argparse
from datetime import datetime
import config  # 파일 상단에 이미 있음(중복 import 불필요)

# 로그인 단계(Selenium) 브라우저 기본값
LOGIN_BROWSER = 'firefox'  # choices: ['firefox', 'chrome']
# 로그인 단계(Selenium) headless 모드 기본값
# LOGIN_HEADLESS = True
# 크롤링 단계(Playwright) headless 모드 기본값
# CRAWLING_HEADLESS = True
# 프록시 사용 여부 기본값
USE_PROXY = True
# ASIN 엑셀 슬라이싱 시작/끝 인덱스 기본값
ASIN_SLICE_START = 0
ASIN_SLICE_END = None
# 각 제품마다 크롤링할 최대 페이지 수 기본값
MAX_PAGES = 10
# Playwright에서 동시에 사용할 context 개수 기본값
MAX_CONCURRENT_CONTEXTS = 10
# 로그 레벨 기본값
LOG_LEVEL = 'DEBUG'

# 현재 작업 디렉토리
CWD = os.getcwd()

# .env 파일에서 환경 변수 로드
load_dotenv(os.path.join(CWD, ".env"))

# 여러 개의 아마존 계정 정보를 .env에서 불러오기
# (이메일::비번 쌍을 콤마로 구분)
AMAZON_ACCOUNTS = os.getenv("AMAZON_ACCOUNTS", "").split(",")

# 계정 쌍 리스트 생성 ([(email, password), ...])
ACCOUNT_PAIRS = []
for acc in AMAZON_ACCOUNTS:
    parts = acc.strip().split("::")
    if len(parts) == 2:
        ACCOUNT_PAIRS.append((parts[0].strip(), parts[1].strip()))

# 사용할 계정 1쌍을 랜덤으로 선택
if ACCOUNT_PAIRS:
    SELECTED_EMAIL, SELECTED_PASSWORD = random.choice(ACCOUNT_PAIRS)
else:
    SELECTED_EMAIL, SELECTED_PASSWORD = "", ""

AMAZON_SITE = "https://www.amazon.com"

# 현재 사용할 계정 정보
AMAZON_LOGIN = {
    "email": SELECTED_EMAIL,
    "password": SELECTED_PASSWORD,
    "site": AMAZON_SITE
}

if not AMAZON_LOGIN["email"] or not AMAZON_LOGIN["password"]:
    print("경고: 아마존 로그인 정보가 환경 변수에 설정되지 않았습니다.")
    print("환경 변수 AMAZON_ACCOUNTS를 이메일::비번 쌍으로 설정하세요.")

# User-Agent 리스트 (브라우저 자동화 탐지 회피용)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_5_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
]

# Firefox 브라우저 프로필 경로
if platform.system().lower().startswith('win'):
    FIREFOX_PROFILE_PATH = r"C:\Users\jmlim2\AppData\Roaming\Mozilla\Firefox\Profiles\gc3co7ov.default-release"
else:
    FIREFOX_PROFILE_PATH = "/home/enssel/.mozilla/firefox/l7mo6xsk.vpn_add"

# 여러 프록시 불러오기
PROXIES = os.getenv("PROXIES", "").split(",")
PROXIES = [p.strip() for p in PROXIES if p.strip()]
# 사용할 프록시 1개 랜덤 선택
# SELECTED_PROXY = random.choice(PROXIES) if PROXIES else None

ORDER_HISTORY_URL = "https://www.amazon.com/gp/css/order-history"
CART_URL = "https://www.amazon.com/gp/cart/view.html"

ORDER_PAGE_LOGIN_SUCCESS_TEXTS = [
    "Your Orders",  # 영어
    # "주문 내역",  # 한글 등 다국어 추가 가능
]
CART_PAGE_LOGIN_SUCCESS_TEXTS = [
    "Your Items",  # 영어
    # "장바구니",  # 한글 등 다국어 추가 가능
]

CART_SIGNIN_BUTTON_SELECTORS = [
    ("xpath", "//a[contains(@href, 'ap/signin') and contains(., 'Sign in to your account')]"),
    # 필요시 추가 selector
]

# [로그인 단계] 이메일 입력란을 찾기 위한 selector 리스트
EMAIL_FIELD_SELECTORS = [
    ("id", "ap_email"),
    ("id", "ap_email_login"),
    ("id", "ap_login"),
    ("name", "email"),
    ("css", "input[type='email']"),
    ("xpath", "//input[@type='email']"),
    ("xpath", "//input[contains(@placeholder, 'email')]"),
    ("xpath", "//input[contains(@placeholder, 'mobile')]"),
    ("xpath", "//div[contains(@class, 'a-section')]//input[contains(@id, 'email') or contains(@id, 'login')]")
]

# [로그인 단계] 이메일 입력 후 '계속(Continue)' 버튼을 찾기 위한 selector 리스트
CONTINUE_BUTTON_SELECTORS = [
    ("id", "continue"),
    ("id", "continue-announce"),
    ("id", "continue-button"),
    ("name", "continue"),
    ("css", "input[type='submit'][id='continue']"),
    ("css", "span#continue"),
    ("xpath", "//input[@id='continue']"),
    ("xpath", "//span[@id='continue']"),
    ("css", "span#continue-announce"),
    ("xpath", "//input[@type='submit' and @id='continue']"),
    ("xpath", "//button[contains(@class, 'a-button-input')]"),
    ("xpath", "//span[contains(text(), 'Continue')]/ancestor::span[contains(@class, 'a-button')]"),
    ("xpath", "//input[@type='submit' or @type='button']")
]

# [로그인 단계] 비밀번호 입력란을 찾기 위한 selector 리스트
PASSWORD_FIELD_SELECTORS = [
    ("id", "ap_password"),
    ("name", "password"),
    ("css", "input[type='password']"),
    ("xpath", "//input[@type='password']"),
    ("xpath", "//input[contains(@id, 'password')]"),
    ("xpath", "//div[contains(@class, 'a-section')]//input[@type='password']")
]

# [로그인 단계] 비밀번호 입력 후 '로그인(SignIn)' 버튼을 찾기 위한 selector 리스트
SIGNIN_BUTTON_SELECTORS = [
    ("id", "signInSubmit"),
    ("id", "sign-in-button"),
    ("name", "signIn"),
    ("css", "input[type='submit'][id='signInSubmit']"),
    ("css", "input.a-button-input"),
    ("xpath", "//input[@id='signInSubmit']"),
    ("xpath", "//input[contains(@class, 'a-button-input')]"),
    ("id", "a-autoid-0"),
    ("css", "span#signInSubmit"),
    ("css", "input[type='submit']"),
    ("xpath", "//span[@id='signInSubmit']"),
    ("xpath", "//span[contains(text(), 'Sign')]/ancestor::span[contains(@class, 'a-button')]"),
    ("xpath", "//span[contains(text(), 'sign')]/ancestor::span[contains(@class, 'a-button')]")
]

# [메인 페이지] 로그인 버튼을 찾기 위한 selector 리스트
LOGIN_BUTTON_SELECTORS = [
    ("css", "div#nav-link-accountList > a"),
    ("css", "a[data-nav-ref='nav_ya_signin']"),
    ("css", "a[data-nav-role='signin']"),
    ("xpath", "//a[.//span[contains(text(), 'Hello, sign in')]]"),
    ("id", "nav-link-accountList-nav-line-1"),
    ("id", "nav-link-accountList"),
]

# 로그인 버튼 후보 selector (WebDriverWait용)
LOGIN_BUTTON_WAIT_SELECTORS = [
    ("css", "a[data-nav-ref='nav_ya_signin']"),
    ("xpath", "//a[contains(@data-nav-role, 'signin')]") ,
    ("xpath", "//a[.//span[contains(text(), 'Hello, sign in')]]"),
    ("id", "nav-link-accountList-nav-line-1"),
    ("id", "nav-link-accountList"),
]

# [전화번호 추가 요청 단계] 전화번호 추가 요청 페이지임을 감지하기 위한 indicator 리스트
# (이 중 하나라도 존재하면 전화번호 추가 요청 페이지로 간주)
PHONE_PAGE_INDICATORS = [
    ("xpath", "//h1[contains(text(), 'Keep hackers out')]") ,
    ("xpath", "//p[contains(text(), 'Add a mobile number')]") ,
    ("id", "ap-account-fixup-phone-skip-link"),
    ("id", "account-fixup-phone-number"),
]

# [전화번호 추가 요청 단계] 'Not now' 등 전화번호 추가 생략(건너뛰기) 버튼 selector 리스트
PHONE_SKIP_BUTTON_SELECTORS = [
    ("id", "ap-account-fixup-phone-skip-link"),
    ("xpath", "//a[contains(text(), 'Not now')]"),
    ("xpath", "//button[contains(text(), 'Not now')]"),
    ("css", "a#ap-account-fixup-phone-skip-link"),
]

# [CAPTCHA 단계] CAPTCHA(자동화 방지 문자) 감지 indicator 리스트
CAPTCHA_INDICATORS = [
    ("xpath", "//input[@id='captchacharacters']"),  # CAPTCHA 입력 필드
    ("xpath", "//div[contains(text(), 'Type the characters you see in this image')]") ,  # CAPTCHA 안내 텍스트
    ("xpath", "//img[contains(@src, 'captcha')]") ,  # CAPTCHA 이미지
    ("css", "input[name='amzn-captcha-verify']"),  # CAPTCHA 입력 필드 (css)
    ("css", "form[action='/errors/validateCaptcha']"),  # CAPTCHA 폼
    ("css", "#captchacharacters"),  # CAPTCHA 문자 입력 필드
    ("css", "img[src*='captcha']"),  # CAPTCHA 이미지
    ("text", "Enter the characters you see below"),  # CAPTCHA 안내 텍스트 (영문)
]

# CAPTCHA 'continue shopping' 버튼 감지용 selector 리스트
CAPTCHA_CONTINUE_SHOPPING_SELECTORS = [
    ("xpath", "//button[contains(text(), 'continue shopping') or contains(text(), 'Continue Shopping') or contains(text(), 'continue') or contains(text(), 'Continue') or contains(text(), 'Click the button below') or contains(text(), 'shopping') or contains(text(), '쇼핑 계속') or contains(text(), '아래 버튼을 클릭') or contains(text(), '아래 버튼') or contains(text(), '계속') or contains(text(), '쇼핑') ]"),
    ("xpath", "//input[@type='submit' and (contains(@value, 'continue shopping') or contains(@value, 'Continue Shopping') or contains(@value, 'continue') or contains(@value, 'Continue'))]"),
    ("xpath", "//a[contains(text(), 'continue shopping') or contains(text(), 'Continue Shopping') or contains(text(), 'continue') or contains(text(), 'Continue') or contains(text(), 'Click the button below') or contains(text(), 'shopping') or contains(text(), '쇼핑 계속') or contains(text(), '아래 버튼을 클릭') or contains(text(), '아래 버튼') or contains(text(), '계속') or contains(text(), '쇼핑') ]"),
]

# [로그인 성공 단계] 로그인 성공을 다양한 방식으로 감지하는 indicator 리스트
LOGIN_SUCCESS_INDICATORS = [
    ("id", "nav-link-accountList"),
    ("id", "nav-your-amazon"),
    ("id", "navbar-main"),
    ("id", "nav-tools"),
    ("xpath", "//span[contains(text(), 'Hello')]"),
    ("xpath", "//a[contains(@href, '/gp/css/homepage')]"),
    ("xpath", "//div[contains(@id, 'navbar')]"),
    ("xpath", "//a[contains(text(), 'Your Account')]"),
    ("xpath", "//div[contains(@class, 'nav-bb-right')]//a[contains(text(), 'Your Account')]"),
    ("css", "div.nav-bb-right"),
    ("id", "navbar-backup-backup"),
    ("xpath", "//a[contains(@href, 'nav_bb_ya') and contains(text(), 'Your Account')]"),
    ("xpath", "//div[@id='navbar-backup-backup']//a[contains(text(), 'Your Account')]"),
    ("xpath", "//div[contains(@class, 'nav-bb-right')]//a[contains(text(), 'Your Account')]"),
    ("xpath", "//a[contains(@href, 'homepage') and contains(text(), 'Your Account')]"),
    ("xpath", "//a[contains(@href, 'nav_bb_ya') and contains(text(), 'Your Account')]"),
    ("css", "div#navbar-backup-backup a[href*='homepage']"),
    ("css", "div.nav-bb-right a[href*='homepage']"),
]

# 새로운 엑셀 형식 ASIN 리스트 파일 경로
ASIN_EXCEL_PATH = "./data/ASIN/amazon_review_open_20250530 (1).xlsx"
SHEET_NAME = "검증대상"

# 기존 JSON 파일 기반 ASIN 리스트 경로 (사전 테스트용) 
ASIN_JSON_PATH = {
    'Internal': './data/ASIN/ASIN_Internal_temp.json',
    'Card': './data/ASIN/ASIN_Card_temp.json',
    'External': './data/ASIN/ASIN_External_temp.json',
}

# AWS WAF(웹 방화벽) 감지용 selector/id/text
AWS_WAF_INDICATORS = [
    ("id", "challenge-container"),
    ("text", "awswaf.com"),
    ("text", "AwsWafIntegration"),
    ("text", "JavaScript is disabled"),
]

# 리뷰 블록(각 리뷰 전체) selector
REVIEW_BLOCK_SELECTORS = [
    ("css", "li[data-hook='review']"), # scrapy 버전 기준
    # ("css", "div[data-hook='review']"), # selenium 버전 기준, 차후에도 필요할 수 있음
    # 필요시 추가
]

REVIEW_TITLE_SELECTORS = [
    # 가장 우선적으로 cr-original-review-content (번역/외국어 리뷰)
    ("css", "a[data-hook='review-title'] span.cr-original-review-content"),
    ("css", "span[data-hook='review-title'] span.cr-original-review-content"),
    # 그 다음 일반 span (단, 평점 span 제외)
    ("css", "a[data-hook='review-title'] > span:not(.a-icon-alt):not(.a-letter-space)"),
    ("css", "span[data-hook='review-title'] > span:not(.a-icon-alt):not(.a-letter-space)"),
    # 혹시라도 cr-original-review-content가 없는 경우, 마지막으로 일반 span
    ("css", "a[data-hook='review-title'] > span"),
    ("css", "span[data-hook='review-title'] > span"),
]

REVIEW_TITLE_LINK_SELECTORS = [
    ("css", "a[data-hook='review-title']"),
    ("css", "span[data-hook='review-title']"),
]

# 리뷰 본문 selector
REVIEW_CONTENT_SELECTORS = [
    ("css", "span[data-hook='review-body'] span.cr-original-review-content"),
    ("css", "span[data-hook='review-body'] span"),
    ("css", "span[data-hook='review-body']"),
    ("css", "div[data-hook='review-collapsed'] span"),
    ("css", "div.review-data span"),
]

# 리뷰 평점
REVIEW_STAR_SELECTORS = [
    # 1. data-hook이 review-star-rating 또는 cmps-review-star-rating인 i 태그 내부의 span.a-icon-alt
    ("css", "i[data-hook='review-star-rating'] span.a-icon-alt"),
    ("css", "i[data-hook='cmps-review-star-rating'] span.a-icon-alt"),
    ("css", "i[data-hook='review-star-rating'] > span.a-icon-alt"),
    ("css", "i[data-hook='cmps-review-star-rating'] > span.a-icon-alt"),
    # 2. class 기반 (a-icon-star, a-star-1~5, review-rating 등)
    ("css", "i.a-icon-star span.a-icon-alt"),
    ("css", "i.review-rating span.a-icon-alt"),
    ("css", "i[class*='a-star-'] span.a-icon-alt"),
    # 3. review-star-rating, cmps-review-star-rating, a-icon-star 등 i 태그 자체의 aria-label
    ("css", "i[data-hook='review-star-rating'][aria-label]"),
    ("css", "i[data-hook='cmps-review-star-rating'][aria-label]"),
    ("css", "i.a-icon-star[aria-label]"),
    # 4. span.a-icon-alt (fallback)
    ("css", "span.a-icon-alt"),
    # 5. XPath fallback (li[data-hook='review'] 내부의 i/span)
    ("xpath", ".//i[contains(@class, 'a-icon-star')]/span[contains(@class, 'a-icon-alt')]")
]

# 리뷰 총 개수(페이지 상단)
REVIEW_COUNT_SELECTORS = [
    ("css", "div[data-hook='cr-filter-info-review-rating-count']"),
    ("xpath", "//div[contains(@data-hook, 'cr-filter-info-review-rating-count')]"),
    # 필요시 추가
]

REVIEW_WRITER_SELECTORS = [
    ("css", "span.a-profile-name"),
]

# 리뷰 작성일
REVIEW_DATE_SELECTORS = [
    ("css", "span[data-hook='review-date']"),
    ("xpath", ".//span[@data-hook='review-date']"),
]

REVIEW_OPTION_SELECTORS = [
    ".//a[@data-hook='format-strip']",
    ".//div[contains(@class, 'review-format-strip')]/a",
    # 필요시 추가 selector
]

REVIEW_OPTION_EXCLUDE_KEYWORDS = [
    "Verified Purchase",
    "What's this?",
    # 필요시 추가
]

REVIEW_VERIFIED_SELECTORS = [
    ".//span[@data-hook='avp-badge' and contains(text(), 'Verified Purchase')]",
    ".//a[@aria-label and contains(@aria-label, 'Verified Purchase')]",
    ".//span[contains(@class, 'a-color-state') and contains(text(), 'Verified Purchase')]",
    # 필요시 추가 selector
]

# 리뷰 helpful vote selector
REVIEW_HELPFUL_SELECTORS = [
    ("css", "span[data-hook='helpful-vote-statement']"),
    ("xpath", ".//span[contains(@data-hook, 'helpful-vote-statement')]"),  # 반드시 .//로!
]

REVIEW_NEXT_PAGE_SELECTORS = [
    ("xpath", "//a[contains(text(), 'Next page')]"),
    ("xpath", "//div[@class='a-text-center']/ul[@class='a-pagination']/li[@class='a-last']/a"),
    ("xpath", "//ul[@class='a-pagination']/li[contains(@class, 'a-last')]/a")
]


# 실패 유형 상수
FAILURE_TYPE_PRODUCT_NO_EXIST = "PRODUCT_NO_EXIST"
FAILURE_TYPE_NO_REVIEWS = "NO_REVIEWS"
FAILURE_TYPE_CRAWLING_ERROR = "CRAWLING_ERROR"
FAILURE_TYPE_OTHER = "OTHER"

# 실패 메시지 상수
FAILURE_MSG_NO_REVIEWS = "제품은 존재하지만 리뷰가 없습니다 (제품 페이지에서 확인)"
FAILURE_MSG_NO_PRODUCT = "제품 자체가 존재하지 않습니다 (제품 페이지 404)"
FAILURE_MSG_CRAWLING_ERROR = "리뷰 데이터 추출 중 오류"
FAILURE_MSG_OTHER = "기타 오류"

# 실패 ASIN 저장 경로(날짜/시간 포맷 활용 가능)
FAILED_ASIN_DIR = "./data/failed"
FAILED_ASIN_FILENAME = f"failed_ASIN_list_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
FAILED_ASIN_PATH = f"{FAILED_ASIN_DIR}/{FAILED_ASIN_FILENAME}"

# 로그 디렉토리 경로 (logger.py와 공유)
LOG_DIR = "./logs"
RUN_TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILENAME = f"amazon_crawler_{RUN_TIMESTAMP}.log"
LOG_FILE_PATH = os.path.join(LOG_DIR, LOG_FILENAME)

# 결과(result) 저장 경로 및 파일명
RESULTS_DIR_PATH = os.path.join(CWD, "data", "results")
RESULTS_FILENAME = f"ASIN_REVIEWS_Excel_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
RESULTS_PATH = f"{RESULTS_DIR_PATH}/{RESULTS_FILENAME}"

# ================= 사용자 행동(스크롤/딜레이) 관련 설정 =================
PAGE_DELAY = 5  # 페이지 간 랜덤 대기 시간(초)
SCROLL_DELAY = 2  # 스크롤 간 대기 시간(초)
SCROLL_INCREMENT = 300  # 스크롤 증가량(픽셀)
WAIT_TIME = 5  # 웹 요소 대기 시간(초)

# 결과물 저장 경로
RESULTS_DIR_PATH = os.path.join(CWD, "data", "results")
FAILED_DIR_PATH = os.path.join(CWD, "data", "failed")
LOG_PATH = os.path.join(CWD, "logs", "crawler.log")

# 실패 유형 상수
FAILURE_TYPE_PRODUCT_NO_EXIST = "PRODUCT_NO_EXIST"
FAILURE_TYPE_NO_REVIEWS = "NO_REVIEWS"
FAILURE_TYPE_CRAWLING_ERROR = "CRAWLING_ERROR"
FAILURE_TYPE_OTHER = "OTHER"

# 실패 메시지 상수
FAILURE_MSG_NO_REVIEWS = "제품은 존재하지만 리뷰가 없습니다 (제품 페이지에서 확인)"
FAILURE_MSG_NO_PRODUCT = "제품 자체가 존재하지 않습니다 (제품 페이지 404)"
FAILURE_MSG_CRAWLING_ERROR = "리뷰 데이터 추출 중 오류"
FAILURE_MSG_OTHER = "기타 오류"

# group_id 추출 시 제외할 키워드
GROUP_ID_EXCLUDE_KEYWORDS = [
    'Verified Purchase',
    'Amazon Vine Customer Review of Free Product',
    "What's this?"
]