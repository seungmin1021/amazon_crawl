"""
Selenium 웹드라이버 설정 및 브라우저 제어
"""
# from selenium import webdriver
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
import random
from config import USER_AGENTS
import time
from selenium.webdriver.common.by import By
import logging
import os

def parse_proxy(proxy):
    # proxy: "http://id:password@ip:port" 또는 "id:password@ip:port"
    if proxy.startswith("http://") or proxy.startswith("https://"):
        proxy = proxy.split("://")[1]
    if "@" in proxy:
        user_pass, host_port = proxy.split("@")
        user, password = user_pass.split(":")
        host, port = host_port.split(":")
        return host, port, user, password
    else:
        host, port = proxy.split(":")
        return host, port, None, None

def setup_chrome_driver(headless=False, proxy=None, logger=None):
    if logger is None:
        logger = logging.getLogger()
    options = ChromeOptions()
    if headless:
        options.add_argument('--headless')
    options.add_argument(f'user-agent={random.choice(USER_AGENTS)}')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--window-size=1200,800')
    if proxy:
        options.add_argument(f'--proxy-server={proxy}')  # 예: "http://123.123.123.123:8080"
    driver = webdriver.Chrome(options=options)
    logger.info(f"[브라우저][setup_chrome_driver] Chrome 드라이버 생성 (headless={headless}, proxy={proxy})")
    return driver

def setup_firefox_driver(headless=False, profile_path=None, proxy=None, logger=None):
    if logger is None:
        logger = logging.getLogger()
    options = Options()
    if headless:
        options.add_argument('--headless')
    seleniumwire_options = None
    if proxy:
        host, port, user, password = parse_proxy(proxy)
        seleniumwire_options = {
            'proxy': {
                'http': f'http://{user}:{password}@{host}:{port}',
                'https': f'http://{user}:{password}@{host}:{port}',
                'no_proxy': 'localhost,127.0.0.1'
            }
        }
    driver = webdriver.Firefox(options=options, seleniumwire_options=seleniumwire_options)
    logger.info(f"[브라우저][setup_firefox_driver] Firefox 드라이버 생성 (headless={headless}, proxy={proxy})")
    return driver

def get_current_ip_info(driver, logger=None):
    if logger is None:
        logger = logging.getLogger()
    """
    현재 브라우저(셀레니움)에서 외부 IP를 ipify.org로 확인합니다.
    Returns:
        str: 외부 IP 주소 (문자열) 또는 에러 메시지
    """
    try:
        driver.get("https://api.ipify.org/")
        time.sleep(random.uniform(1, 2))  # 페이지 로딩 대기
        ip = driver.find_element(By.TAG_NAME, "body").text.strip()
        logger.info(f"[브라우저][get_current_ip_info] VPN/프록시 정보 (ipify.org): {ip}")
        return ip
    except Exception as e:
        logger.warning(f"[브라우저][get_current_ip_info] ipify.org에서 IP 확인 실패: {str(e)}")
        return f"error: {e}"
