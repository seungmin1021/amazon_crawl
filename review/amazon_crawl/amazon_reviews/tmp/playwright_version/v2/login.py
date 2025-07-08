"""
아마존 로그인 처리 모듈 (전화번호 추가 요청 대응, 한글자/두글자/세글자 랜덤 분할 입력, config 기반)
"""
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
from config import (
    AMAZON_LOGIN,
    CART_PAGE_LOGIN_SUCCESS_TEXTS,
    CART_SIGNIN_BUTTON_SELECTORS,
    CART_URL,
    EMAIL_FIELD_SELECTORS,
    CONTINUE_BUTTON_SELECTORS,
    ORDER_HISTORY_URL,
    ORDER_PAGE_LOGIN_SUCCESS_TEXTS,
    PASSWORD_FIELD_SELECTORS,
    SIGNIN_BUTTON_SELECTORS,
    LOGIN_BUTTON_SELECTORS,
    PHONE_PAGE_INDICATORS,
    PHONE_SKIP_BUTTON_SELECTORS,
    CAPTCHA_INDICATORS,
    LOGIN_SUCCESS_INDICATORS,
    LOGIN_BUTTON_WAIT_SELECTORS,
    AWS_WAF_INDICATORS
)

from utils import wait_for_page_load

def random_sleep(a=0.5, b=1.5, logger=None):
    if logger is None:
        logger = logging.getLogger()
    t = random.uniform(a, b)
    logger.debug(f"랜덤 대기: {t:.2f}초")
    time.sleep(t)
    return t

def slow_typing(element, text, min_delay=0.05, max_delay=0.2, logger=None):
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(min_delay, max_delay))

def random_chunks(s):
    chunks = []
    i = 0
    while i < len(s):
        chunk_size = random.choice([1, 2, 3, 4])
        chunk = s[i:i+chunk_size]
        chunks.append(chunk)
        i += chunk_size
    return chunks

def find_element_with_selectors(driver, selectors, timeout=15, desc=None, check_displayed=True, logger=None):
    if logger is None:
        logger = logging.getLogger()
    wait = WebDriverWait(driver, timeout)
    for sel_type, sel_value in selectors:
        try:
            if sel_type == "id":
                el = wait.until(EC.presence_of_element_located((By.ID, sel_value)))
                # div#nav-link-accountList라면 내부 a를 반환
                if sel_value == "nav-link-accountList" and el.tag_name == "div":
                    try:
                        a_tag = el.find_element(By.TAG_NAME, "a")
                        if a_tag and a_tag.is_displayed():
                            logger.info(f"[요소] {desc or ''} (div#{sel_value} > a) 찾음")
                            return a_tag
                    except Exception:
                        pass
            elif sel_type == "name":
                el = wait.until(EC.presence_of_element_located((By.NAME, sel_value)))
            elif sel_type == "css":
                el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, sel_value)))
            elif sel_type == "xpath":
                el = wait.until(EC.presence_of_element_located((By.XPATH, sel_value)))
            else:
                continue
            # check_displayed 옵션에 따라 분기
            if not check_displayed or (el and el.is_displayed()):
                logger.info(f"[요소] {desc or ''} ({sel_type} {sel_value}) 찾음")
                return el
        except Exception:
            # 예외 발생 시 별도 로그 남기지 않음(불필요한 warning 방지)
            continue
    # 모든 selector를 시도해도 못 찾았을 때만 warning
    logger.warning(f"[요소] {desc or ''}를 찾지 못함")
    return None

def is_phone_page(driver):
    for sel_type, sel_value in PHONE_PAGE_INDICATORS:
        try:
            if sel_type == "id":
                if driver.find_elements(By.ID, sel_value):
                    return True
            elif sel_type == "xpath":
                if driver.find_elements(By.XPATH, sel_value):
                    return True
        except Exception:
            continue
    return False

def click_phone_skip(driver, timeout=10, logger=None):
    btn = find_element_with_selectors(driver, PHONE_SKIP_BUTTON_SELECTORS, timeout, desc="전화번호 추가 생략(건너뛰기) 버튼", logger=logger)
    if btn:
        logger.info("[로그인] 전화번호 추가 생략(건너뛰기) 버튼 클릭")
        btn.click()

        # 페이지 로드까지 대기
        wait_for_page_load(driver)

        t = random_sleep(2, 3, logger=logger)
        logger.debug(f"[로그인] 전화번호 추가 생략 버튼 클릭 후 대기: {t:.2f}초")
        return True
    else:
        logger.warning("[로그인] 전화번호 추가 생략(건너뛰기) 버튼을 찾을 수 없습니다.")
        return False

def is_captcha_page(driver):
    """
    config.CAPTCHA_PAGE_INDICATORS 기반으로 CAPTCHA 감지
    """
    try:
        for sel_type, sel_value in CAPTCHA_INDICATORS:
            if sel_type == "id":
                if driver.find_elements(By.ID, sel_value):
                    return True
            elif sel_type == "css":
                if driver.find_elements(By.CSS_SELECTOR, sel_value):
                    return True
            elif sel_type == "xpath":
                if driver.find_elements(By.XPATH, sel_value):
                    return True
            elif sel_type == "text":
                if sel_value in driver.page_source:
                    return True
        return False
    except Exception:
        return False

def is_aws_waf(driver):
    """
    config.AWS_WAF_INDICATORS 기반으로 AWS WAF 감지
    """
    try:
        for sel_type, sel_value in AWS_WAF_INDICATORS:
            if sel_type == "id":
                if driver.find_elements(By.ID, sel_value):
                    return True
            elif sel_type == "css":
                if driver.find_elements(By.CSS_SELECTOR, sel_value):
                    return True
            elif sel_type == "xpath":
                if driver.find_elements(By.XPATH, sel_value):
                    return True
            elif sel_type == "text":
                if sel_value in driver.page_source:
                    return True
        return False
    except Exception:
        return False

def go_to_login_page(driver, timeout=15, logger=None):
    if logger is None:
        logger = logging.getLogger()
    logger.info("[로그인] 아마존 메인 페이지로 이동")
    driver.get(AMAZON_LOGIN['site'])
    logger.info(f"[로그인] 메인 페이지 이동 후: {driver.current_url}")

    # 페이지 로드까지 대기
    wait_for_page_load(driver)
    logger.info(f"[로그인] 페이지 로드 대기 후: {driver.current_url}")

    # 세션/쿠키/스토리지 초기화
    driver.delete_all_cookies()
    driver.execute_script("window.localStorage.clear();")
    driver.execute_script("window.sessionStorage.clear();")
    logger.info(f"[로그인] 쿠키/스토리지 초기화 후: {driver.current_url}")
    driver.refresh()
    logger.info(f"[로그인] driver.refresh() 후: {driver.current_url}")

    # driver.refresh() 후 현재 페이지 HTML 저장
    try:
        import os
        os.makedirs("./html", exist_ok=True)
        html_source = driver.page_source
        with open("./html/amazon_login_debug.html", "w", encoding="utf-8") as f:
            f.write(html_source)
        logger.info(f"[로그인] driver.refresh() 후 HTML을 ./html/amazon_login_debug.html로 저장 완료 [URL: {driver.current_url}]")
    except Exception as e:
        logger.error(f"[로그인] HTML 저장 중 오류 발생: {e} [URL: {driver.current_url}]")

    # AWS WAF 감지 추가 (driver.refresh() 후 바로)
    if is_aws_waf(driver):
        logger.error(f"[로그인] AWS WAF(웹 방화벽) 챌린지 페이지 감지됨. 자동화가 차단되었습니다. [URL: {driver.current_url}]")
        print(f"\n[AWS WAF] 아래 URL을 브라우저에 붙여넣어 직접 확인하거나, 프록시/환경을 변경해 재시도하세요:\n{driver.current_url}\n")
        return False

    # CAPTCHA 감지 및 처리 (통합)
    if not handle_captcha(driver, timeout=60, logger=logger):
        return False

    # 로그인 버튼 탐색 ㅣ제전 WebDriverWait + 랜덤 sleep 적용
    try:
        WebDriverWait(driver, 10).until(
            lambda d: any(
                d.find_elements(*{
                    "id": (By.ID, sel),
                    "css": (By.CSS_SELECTOR, sel),
                    "xpath": (By.XPATH, sel),
                    "name": (By.NAME, sel)
                }[sel_type])
                for sel_type, sel in LOGIN_BUTTON_WAIT_SELECTORS
            )
        )
        logger.info(f"[로그인] 로그인 버튼 후보 selector가 DOM에 등장함을 확인 [URL: {driver.current_url}]")
    except Exception:
        logger.warning(f"[로그인] WebDriverWait으로도 로그인 버튼 후보가 나타나지 않음 [URL: {driver.current_url}]")
    t = random.uniform(2, 3)
    logger.debug(f"[로그인] 로그인 버튼 탐색 전 추가 대기: {t:.2f}초 [URL: {driver.current_url}]")
    time.sleep(t)

    login_btn = find_element_with_selectors(driver, LOGIN_BUTTON_SELECTORS, timeout, desc="로그인 버튼", logger=logger)
    logger.info(f"[로그인] 로그인 버튼 탐색 후 URL: {driver.current_url}")
    if login_btn:
        logger.info(f"[로그인] 로그인 버튼 클릭 [URL: {driver.current_url}]")
        login_btn.click()

        # 페이지 로드까지 대기
        wait_for_page_load(driver)
        logger.info(f"[로그인] 로그인 버튼 클릭 후 페이지 로드 대기: {driver.current_url}")

        t = random_sleep(2, 4, logger=logger)
        logger.debug(f"[로그인] 로그인 버튼 클릭 후 대기: {t:.2f}초 [URL: {driver.current_url}]")
        logger.info(f"[로그인] 로그인 버튼 클릭 후 URL: {driver.current_url}")
        return True
    else:
        # AWS WAF 감지 추가
        if is_aws_waf(driver):
            logger.error(f"[로그인] AWS WAF(웹 방화벽) 챌린지 페이지 감지됨. 자동화가 차단되었습니다. [URL: {driver.current_url}]")
            print(f"\n[AWS WAF] 아래 URL을 브라우저에 붙여넣어 직접 확인하거나, 프록시/환경을 변경해 재시도하세요:\n{driver.current_url}\n")
            return False
        logger.warning(f"[로그인] 로그인 버튼을 찾을 수 없습니다. [URL: {driver.current_url}]")
        
        # 1. Returns & Orders 페이지로 이동
        driver.get(ORDER_HISTORY_URL)
        wait_for_page_load(driver)
        logger.info(f"[로그인] Returns & Orders 페이지 이동: {driver.current_url}")

        # 이메일 입력란 탐색
        email_input = find_element_with_selectors(driver, EMAIL_FIELD_SELECTORS, timeout, desc="이메일 입력란", logger=logger)
        if email_input:
            logger.info("[로그인] Returns & Orders 페이지에서 이메일 입력란 발견, 로그인 시도 가능")
            return True  # 이후 amazon_login에서 기존대로 이메일/비밀번호 입력 진행
        
        # 이미 로그인된 경우: "Your Orders" 텍스트 확인
        if any(txt in driver.page_source for txt in ORDER_PAGE_LOGIN_SUCCESS_TEXTS) and not email_input:
            logger.info("[로그인] Returns & Orders 페이지에서 이미 로그인된 상태로 감지")
            return True  # 이미 로그인 상태

        # 2. 장바구니 페이지로 이동
        driver.get(CART_URL)
        wait_for_page_load(driver)
        logger.info(f"[로그인] Cart 페이지 이동: {driver.current_url}")

        sign_in_btn = find_element_with_selectors(driver, CART_SIGNIN_BUTTON_SELECTORS, timeout, desc="Cart Sign in 버튼", logger=logger)
        if sign_in_btn:
            logger.info("[로그인] Cart 페이지에서 'Sign in to your account' 버튼 발견, 클릭하여 로그인 시도")
            sign_in_btn.click()
            wait_for_page_load(driver)
            return True

        if any(txt in driver.page_source for txt in CART_PAGE_LOGIN_SUCCESS_TEXTS):
            logger.info("[로그인] Cart 페이지에서 이미 로그인된 상태로 감지")
            return True

        # 위 모든 시도 실패 시
        logger.error("[로그인] Returns & Orders/Cart 페이지에서도 로그인 진입 실패")
        return False

def handle_captcha(driver, timeout=60, logger=None):
    """
    CAPTCHA_INDICATORS 기반으로 CAPTCHA 감지 및 수동 해결 대기
    감지되면 URL 안내, 60초 대기, 해결 시 True, 미해결 시 False 반환
    """
    if logger is None:
        logger = logging.getLogger()
    # CAPTCHA 감지
    found = False
    for sel_type, sel_value in CAPTCHA_INDICATORS:
        try:
            if sel_type == "id":
                if driver.find_elements(By.ID, sel_value):
                    found = True
                    break
            elif sel_type == "css":
                if driver.find_elements(By.CSS_SELECTOR, sel_value):
                    found = True
                    break
            elif sel_type == "xpath":
                if driver.find_elements(By.XPATH, sel_value):
                    found = True
                    break
            elif sel_type == "text":
                if sel_value in driver.page_source:
                    found = True
                    break
        except Exception:
            continue
    if not found:
        logger.info("[로그인] CAPTCHA 감지 안됨, 정상 진행")
        return True
    # CAPTCHA 감지됨
    logger.error(f'[로그인] CAPTCHA 페이지 감지됨. 자동화가 차단되었습니다. [URL: {driver.current_url}]')
    print(f"\n[CAPTCHA] 아래 URL을 브라우저에 붙여넣어 직접 해결하세요:\n{driver.current_url}\n")
    print(f"[CAPTCHA] {timeout}초 내에 CAPTCHA를 직접 해결하면 자동으로 진행됩니다.")
    start_time = time.time()
    while time.time() - start_time < timeout:
        time.sleep(2)
        # CAPTCHA indicator가 모두 사라졌는지 재확인
        still_captcha = False
        for sel_type, sel_value in CAPTCHA_INDICATORS:
            try:
                if sel_type == "id" and driver.find_elements(By.ID, sel_value):
                    still_captcha = True
                    break
                elif sel_type == "css" and driver.find_elements(By.CSS_SELECTOR, sel_value):
                    still_captcha = True
                    break
                elif sel_type == "xpath" and driver.find_elements(By.XPATH, sel_value):
                    still_captcha = True
                    break
                elif sel_type == "text" and sel_value in driver.page_source:
                    still_captcha = True
                    break
            except Exception:
                continue
        if not still_captcha:
            logger.info("[로그인] CAPTCHA가 해결되어 자동화가 재개됩니다.")
            return True
    logger.error(f"[로그인] {timeout}초 내에 CAPTCHA가 해결되지 않아 종료합니다.")
    return False

def click_with_fallback(element, driver, desc="버튼/입력 제출", fallback_element=None, logger=None):
    if logger is None:
        logger = logging.getLogger()
    try:
        element.click()

        # 페이지 로드까지 대기
        wait_for_page_load(driver)

        logger.info(f"[로그인] {desc} 클릭 완료")
        return True
    except Exception:
        logger.debug(f"[로그인] {desc} 클릭 불가, ENTER 키 시도")
        try:
            element.send_keys(Keys.RETURN)
            logger.info(f"[로그인] {desc} ENTER 키 입력 완료")
            return True
        except Exception:
            logger.debug(f"[로그인] {desc} ENTER 입력 불가, JS form 제출 시도")
            try:
                driver.execute_script("document.querySelector('form').submit();")
                logger.info(f"[로그인] {desc} JS form 제출 완료")
                return True
            except Exception:
                logger.error(f"[로그인] {desc} JS form 제출 불가")
                return False

def is_login_success(driver, logger=None):
    el = find_element_with_selectors(driver, LOGIN_SUCCESS_INDICATORS, timeout=5, desc="로그인 성공 indicator", check_displayed=False, logger=logger)
    if el:
        try:
            if "Your Account" in el.text:
                return True
        except Exception:
            pass
        return True
    # 보조: page_source에서 직접 텍스트 탐색
    if "Your Account" in driver.page_source:
        return True
    return False

def amazon_login(driver, email=None, password=None, timeout=30, logger=None):
    if logger is None:
        logger = logging.getLogger()
    email = email or AMAZON_LOGIN["email"]
    password = password or AMAZON_LOGIN["password"]
    
    logger.info(f"[로그인] 랜덤으로 선택된 EMAIL: {email} [URL: {driver.current_url}]")
    logger.info(f"[로그인] 아마존 로그인 페이지 진입 시도 [URL: {driver.current_url}]")

    # 로그인 버튼이 없을 때, 이미 로그인된 상태인지 추가로 확인
    # if is_login_success(driver):
    #     logger.info("[로그인] 로그인 버튼이 없으나, 계정 indicator(Your Account 등)가 감지되어 이미 로그인된 상태로 간주합니다.")
    #     return True

    # AWS WAF 감지 추가
    if is_aws_waf(driver):
        logger.error(f"[로그인] AWS WAF(웹 방화벽) 챌린지 페이지 감지됨. 자동화가 차단되었습니다. [URL: {driver.current_url}]")
        print(f"\n[AWS WAF] 아래 URL을 브라우저에 붙여넣어 직접 확인하거나, 프록시/환경을 변경해 재시도하세요:\n{driver.current_url}\n")
        return False

    if not go_to_login_page(driver, timeout, logger=logger):
        logger.error(f"[로그인] 로그인 폼 진입 불가 [URL: {driver.current_url}]")
        return False
    try:
        t = random_sleep(2, 4, logger=logger)
        logger.debug(f"로그인 페이지 진입 후 대기: {t:.2f}초 [URL: {driver.current_url}]")
        logger.info(f"[로그인] 로그인 페이지 진입 후 URL: {driver.current_url}")
        email_input = find_element_with_selectors(driver, EMAIL_FIELD_SELECTORS, timeout, desc="이메일 입력란", logger=logger)
        logger.info(f"[로그인] 이메일 입력란 탐색 후 URL: {driver.current_url}")
        if not email_input:
            logger.error(f"[로그인] 이메일 입력란을 찾지 못함 [URL: {driver.current_url}]")
            return False
        email_input.clear()
        email_chunks = random_chunks(email)
        logger.info(f"[로그인] 이메일 입력 시작 [URL: {driver.current_url}]")
        for chunk in email_chunks:
            slow_typing(email_input, chunk, 0.07, 0.18, logger=logger)
            random_sleep(0.2, 0.7, logger=logger)
        random_sleep(0.5, 1.2, logger=logger)
        logger.info(f"[로그인] 이메일 입력 완료 [URL: {driver.current_url}]")
        logger.info(f"[로그인] 이메일 입력 후 URL: {driver.current_url}")
        continue_btn = find_element_with_selectors(driver, CONTINUE_BUTTON_SELECTORS, timeout, desc="이메일 제출(계속) 버튼", logger=logger)
        logger.info(f"[로그인] 계속 버튼 탐색 후 URL: {driver.current_url}")
        if not continue_btn:
            logger.error(f"[로그인] 이메일 제출(계속) 버튼을 찾지 못함 [URL: {driver.current_url}]")
            return False
        random_sleep(0.5, 1.5, logger=logger)
        if not click_with_fallback(continue_btn, driver, desc="이메일 제출(계속) 버튼", fallback_element=email_input, logger=logger):
            logger.error(f"[로그인] 이메일 제출(계속) 버튼 클릭/ENTER/JS 모두 불가 [URL: {driver.current_url}]")
            return False
        random_sleep(1, 2.5, logger=logger)
        logger.info(f"[로그인] 계속 버튼 클릭 후 URL: {driver.current_url}")
        if not handle_captcha(driver, timeout=60, logger=logger):
            logger.error(f"[로그인] CAPTCHA 처리 실패 [URL: {driver.current_url}]")
            return False
        logger.info(f"[로그인] CAPTCHA 처리 후 URL: {driver.current_url}")
        password_input = find_element_with_selectors(driver, PASSWORD_FIELD_SELECTORS, timeout, desc="비밀번호 입력란", logger=logger)
        logger.info(f"[로그인] 비밀번호 입력란 탐색 후 URL: {driver.current_url}")
        if not password_input:
            logger.error(f"[로그인] 비밀번호 입력란을 찾지 못함 [URL: {driver.current_url}]")
            return False
        password_input.clear()
        pw_chunks = random_chunks(password)
        logger.info(f"[로그인] 비밀번호 입력 시작 [URL: {driver.current_url}]")
        for chunk in pw_chunks:
            slow_typing(password_input, chunk, 0.07, 0.15, logger=logger)
            random_sleep(0.2, 0.6, logger=logger)
        random_sleep(0.5, 1.2, logger=logger)
        logger.info(f"[로그인] 비밀번호 입력 완료 [URL: {driver.current_url}]")
        logger.info(f"[로그인] 비밀번호 입력 후 URL: {driver.current_url}")
        sign_in_btn = find_element_with_selectors(driver, SIGNIN_BUTTON_SELECTORS, timeout, desc="로그인(SignIn) 버튼", logger=logger)
        logger.info(f"[로그인] 로그인 버튼 탐색 후 URL: {driver.current_url}")
        if not sign_in_btn:
            logger.error(f"[로그인] 로그인(SignIn) 버튼을 찾지 못함 [URL: {driver.current_url}]")
            return False
        random_sleep(0.5, 1.5, logger=logger)
        if not click_with_fallback(sign_in_btn, driver, desc="로그인(SignIn) 버튼", fallback_element=password_input, logger=logger):
            logger.error(f"[로그인] 로그인(SignIn) 버튼 클릭/ENTER/JS 모두 불가 [URL: {driver.current_url}]")
            return False
        random_sleep(2, 3.5, logger=logger)
        logger.info(f"[로그인] 로그인 버튼 클릭 후 URL: {driver.current_url}")
        if not handle_captcha(driver, timeout=60, logger=logger):
            logger.error(f"[로그인] CAPTCHA 처리 실패 [URL: {driver.current_url}]")
            return False
        logger.info(f"[로그인] (로그인 버튼 이후) CAPTCHA 처리 후 URL: {driver.current_url}")
        if is_phone_page(driver):
            logger.info(f"[로그인] 전화번호 추가 요청 페이지 감지됨. 'Not now' 버튼 클릭 시도 [URL: {driver.current_url}]")
            logger.info(f"[로그인] 전화번호 추가 요청 페이지 감지 URL: {driver.current_url}")
            if not click_phone_skip(driver, logger=logger):
                logger.error(f"[로그인] 전화번호 추가 생략(건너뛰기) 불가. 수동 조치 필요. [URL: {driver.current_url}]")
                return False
            logger.info(f"[로그인] 전화번호 추가 생략(건너뛰기) 후 URL: {driver.current_url}")
        if is_login_success(driver, logger=logger):
            logger.info(f"[로그인] 아마존 로그인 성공! [URL: {driver.current_url}]")
            logger.info(f"[로그인] 로그인 성공 후 URL: {driver.current_url}")
            return True
        if "authentication required" in driver.page_source.lower():
            logger.error(f"[로그인] 추가 인증 필요. 수동 인증 필요할 수 있음. [URL: {driver.current_url}]")
            logger.info(f"[로그인] 추가 인증 필요 URL: {driver.current_url}")
            return False
        if "There was a problem" in driver.page_source:
            logger.error(f"[로그인] 로그인 불가: 이메일/비밀번호 오류 또는 추가 인증 필요 [URL: {driver.current_url}]")
            logger.info(f"[로그인] 로그인 불가(There was a problem) URL: {driver.current_url}")
            return False
        if ("Looking for Something?" in driver.page_source or
            "ap_error_page_title" in driver.page_source or
            driver.title == "Amazon.com - Page Not Found"):
            logger.error(f"[로그인] 로그인 중 404/에러 페이지 감지 [URL: {driver.current_url}]")
            logger.info(f"[로그인] 404/에러 페이지 감지 URL: {driver.current_url}")
            return False
        logger.error(f"[로그인] 로그인 성공 신호를 감지하지 못함 [URL: {driver.current_url}]")
        logger.info(f"[로그인] 로그인 성공 신호 미감지 URL: {driver.current_url}")
        return False
    except Exception as e:
        logger.error(f"[로그인] 로그인 과정 중 예외 발생: {str(e)} [URL: {driver.current_url}]")
        logger.info(f"[로그인] 예외 발생 시점 URL: {driver.current_url}")
        return False
