"""
아마존 로그인 테스트용 메인 실행 파일
"""
import argparse
from browser import setup_chrome_driver, setup_firefox_driver, get_current_ip_info
from login import amazon_login
from logger import setup_logger
import sys
from selenium import webdriver
from config import USER_AGENTS, FIREFOX_PROFILE_PATH, PROXIES
import random
import config
from utils import load_asin_info_from_excel
from timer import CrawlTimer
from crawler import crawl_reviews_for_asin_list_playwright
import asyncio
import logging
from datetime import datetime
import os

def parse_arguments():
    parser = argparse.ArgumentParser(description="아마존 크롤링 시스템 세팅")
    parser.add_argument('--login_browser', type=str, default=config.LOGIN_BROWSER, choices=['firefox','chrome'], help='로그인 단계(Selenium 기반)에서 사용할 브라우저')
    parser.add_argument('--login_headless', action='store_true', default=config.LOGIN_HEADLESS, help='로그인 단계(Selenium 기반)에서 headless 모드 사용')
    # parser.add_argument('--firefox_profile_path', type=str, default=FIREFOX_PROFILE_PATH, help='VPN 등 확장 프로그램이 적용된 Firefox 프로필 경로')
    parser.add_argument('--use_proxy', action='store_true', default=config.USE_PROXY, help='프록시 서버를 사용할지 여부')
    parser.add_argument('--asin_start', type=int, default=config.ASIN_SLICE_START, help='ASIN 엑셀에서 시작 인덱스 (0부터 시작, 기본값: config.ASIN_SLICE_START)')
    parser.add_argument('--asin_end', type=int, default=config.ASIN_SLICE_END, help='ASIN 엑셀에서 끝 인덱스 (기본값: config.ASIN_SLICE_END)')
    parser.add_argument('--max_pages', type=int, default=config.MAX_PAGES, help=f'각 제품마다 크롤링할 최대 페이지 수 (기본값: {config.MAX_PAGES})')
    parser.add_argument('--crawling_headless', action='store_true', default=config.CRAWLING_HEADLESS, help='리뷰 크롤링 단계(Playwright 기반)에서 headless 모드 사용')
    parser.add_argument('--max_concurrent_contexts', type=int, default=config.MAX_CONCURRENT_CONTEXTS, help='Playwright에서 동시에 사용할 context 개수')
    parser.add_argument('--log_level', type=str, default=config.LOG_LEVEL, help='로그 레벨 설정 (DEBUG, INFO, WARNING, ERROR, CRITICAL)')
    return parser.parse_args()

def get_selenium_cookies_headers(driver):
    # Selenium 쿠키를 Scrapy용 dict로 변환
    cookies = {c['name']: c['value'] for c in driver.get_cookies()}
    # 미국 환경에 맞는 anti-bot 헤더
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'DNT': '1',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-User': '?1',
        'Sec-Fetch-Dest': 'document',
        # 필요시 추가 헤더
    }
    return cookies, headers

def main():
    args = parse_arguments()

    now_str = datetime.now().strftime("%Y%m%d%H%M%S")
    reviews_output_path = os.path.join(config.RESULTS_DIR_PATH, f"ASIN_REVIEWS_Excel_{now_str}.json")
    failed_output_path = os.path.join(config.FAILED_DIR_PATH, f"failed_ASIN_list_{now_str}.json")
    timer_output_path = os.path.join(config.RESULTS_DIR_PATH, f"ASIN_REVIEWS_Excel_{now_str}_timer.json")
    
    timer = CrawlTimer()
    timer.start()

    log_level = getattr(logging, args.log_level.upper(), logging.INFO)
    logger = setup_logger(log_level=log_level)
    logger.info(f"[메인][브라우저] 로그인 브라우저: {args.login_browser}, Login Headless: {args.login_headless}")

    # 프록시 선택
    proxy = None
    if args.use_proxy:
        if PROXIES:
            proxy = random.choice(PROXIES)
            logger.info(f"[메인][프록시] 랜덤으로 선택된 프록시 IP: {proxy}")
        else:
            logger.warning("[메인][프록시] 프록시 목록이 비어 있습니다. 프록시 없이 진행합니다.")
    else:
        logger.info("[메인][프록시] 프록시 미사용(내 IP로 접속)")

    # 드라이버 세팅
    if args.login_browser == 'firefox':
        # driver = setup_firefox_driver(headless=args.headless, profile_path=args.firefox_profile_path, proxy=args.proxy)
        driver = setup_firefox_driver(headless=args.login_headless, proxy=proxy, logger=logger)
    else:
        driver = setup_chrome_driver(headless=args.login_headless, proxy=proxy, logger=logger)

    try:
        # 선택된 프록시 IP
        # logger.info(f"랜덤으로 선택된 프록시 IP: {proxy}")

        # 프록시 or VPN IP 정보
        ip_info = get_current_ip_info(driver)
        logger.info(f"[메인][프록시] VPN/프록시 정보 확인(ipify.org): {ip_info}")

        success = amazon_login(driver, logger=logger)
        if not success:
            logger.error("로그인 실패. 프로그램 종료.")
            sys.exit(1)
        logger.info("[로그인] 로그인 성공.")
        # 2. 쿠키/헤더 추출
        cookies, headers = get_selenium_cookies_headers(driver)
        # 로그인 세션 쿠키/헤더 정보 로그로 출력
        logger.info(f"[로그인][쿠키 정보] {cookies}")
        logger.info(f"[로그인][헤더 정보] {headers}")

        # 엑셀 파일에서 ASIN 목록 로드
        excel_path = config.ASIN_EXCEL_PATH
        sheet_name = config.SHEET_NAME
        asin_info = load_asin_info_from_excel(excel_path, sheet_name, logger=logger)
        # ASIN 슬라이싱 적용
        asin_start = args.asin_start if args.asin_start is not None else config.ASIN_SLICE_START
        asin_end = args.asin_end if args.asin_end is not None else config.ASIN_SLICE_END
        asin_info = asin_info[asin_start:asin_end]
        logger.info(f"[로드] ASIN 슬라이싱 범위: {asin_start} ~ {asin_end}, 실제 로드된 ASIN 개수: {len(asin_info)}")

        # Playwright 기반 크롤러 호출
        all_results, failed_info = asyncio.run(crawl_reviews_for_asin_list_playwright(
            cookies, asin_info,
            reviews_output_path=reviews_output_path,
            failed_output_path=failed_output_path,
            max_pages=args.max_pages,
            headless=args.crawling_headless, max_concurrent_contexts=args.max_concurrent_contexts,
            logger=logger
        ))
        timer.stop()

        success_count = len(asin_info) - len(failed_info)
        timer.set_total_asins(len(asin_info), success_count=success_count, failure_count=len(failed_info))

        timer.set_total_reviews(sum([r.get("crawl_review_cnt", 0) for r in all_results]))
        timer.save(timer_output_path)
        driver.quit()
        sys.exit(0)
    except Exception as e:
        timer.stop()
        # timer.set_total_requests(getattr(driver, 'request_count', 0))
        if 'asin_info' in locals() and 'failed_info' in locals():
            actual_success_count = len(asin_info) - len(failed_info)
            failure_count = len(failed_info)
            timer.set_total_asins(len(asin_info), success_count=actual_success_count, failure_count=failure_count)
        elif 'asin_info' in locals():
            timer.set_total_asins(len(asin_info))

        if 'all_results' in locals():
            timer.set_total_reviews(sum([r.get("crawl_review_cnt", 0) for r in all_results]))
        
        timer.save()
        logger.error(f"[오류] 오류 발생: {e}")
        sys.exit(1)
    finally:
        logger.info("[브라우저] 브라우저 종료.")
        driver.quit()

if __name__ == "__main__":
    main()
