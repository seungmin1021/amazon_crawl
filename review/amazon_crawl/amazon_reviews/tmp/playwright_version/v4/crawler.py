"""
아마존 리뷰 크롤링 (Playwright Only)
- Selenium에서 로그인 후 쿠키를 Playwright로 전달받아 세션 유지
- 여러 ASIN을 비동기 병렬로 크롤링
- config.py의 셀렉터를 그대로 사용
"""
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
import logging
from utils import save_results_to_json, save_failed_asin
from config import (
    AMAZON_SITE, FAILURE_TYPE_CRAWLING_ERROR, GROUP_ID_EXCLUDE_KEYWORDS, REVIEW_BLOCK_SELECTORS, REVIEW_COUNT_SELECTORS, REVIEW_TITLE_SELECTORS, REVIEW_TITLE_LINK_SELECTORS,
    REVIEW_CONTENT_SELECTORS, REVIEW_STAR_SELECTORS, REVIEW_WRITER_SELECTORS, REVIEW_DATE_SELECTORS,
    REVIEW_OPTION_SELECTORS, REVIEW_OPTION_EXCLUDE_KEYWORDS, REVIEW_VERIFIED_SELECTORS, REVIEW_HELPFUL_SELECTORS,
    REVIEW_NEXT_PAGE_SELECTORS, MAX_PAGES, FAILURE_TYPE_NO_REVIEWS, FAILURE_TYPE_PRODUCT_NO_EXIST, FAILURE_TYPE_OTHER,
    FAILURE_MSG_NO_REVIEWS, FAILURE_MSG_NO_PRODUCT, FAILURE_MSG_CRAWLING_ERROR, FAILURE_MSG_OTHER, FAILED_ASIN_PATH,
    PAGE_DELAY, SCROLL_DELAY, SCROLL_INCREMENT, WAIT_TIME, RESULTS_PATH
)
import random
from extractors_playwright import (
    extract_review_blocks, extract_review_title, extract_review_content, extract_review_url, extract_writer_name, extract_option, extract_is_verified, extract_first_text_by_selectors, parse_helpful, extract_review_star, extract_next_page_btn,
    extract_review_count, extract_group_id, extract_write_dt
)

# Selenium 쿠키를 Playwright 쿠키 포맷으로 변환
def selenium_cookies_to_playwright(selenium_cookies, domain=".amazon.com"):
    cookies = []
    for name, value in selenium_cookies.items():
        cookies.append({
            "name": name,
            "value": value,
            "domain": domain,
            "path": "/"
        })
    return cookies

async def crawl_reviews_for_asin_context(browser, selenium_cookies, asin, meta_info, timer, max_pages=MAX_PAGES, logger=None):
    if logger is None:
        logger = logging.getLogger()

    reviews = []
    failed_reason = None
    failure_type = None
    base_url = f"{AMAZON_SITE}/product-reviews/{asin}"
    page_num = 1
    review_cnt = 0  # 리뷰 총 개수 초기화
    context = await browser.new_context()
    cookies = selenium_cookies_to_playwright(selenium_cookies)
    await context.add_cookies(cookies)
    page = await context.new_page()
    try:
        while page_num <= max_pages:
            if page_num == 1:
                review_page_url = f"{base_url}/ref=cm_cr_arp_d_viewopt_srt?ie=UTF8&reviewerType=all_reviews&sortBy=recent&pageNumber=1"
                await page.goto(review_page_url)
                await timer.increment_requests()
                logger.info(f"ASIN {asin} - 첫번째 리뷰 페이지 요청. 현재 총 요청 수: {timer.data['total_requests']}")
                
                # 리뷰 총 개수 추출
                review_cnt = await extract_review_count(page, REVIEW_COUNT_SELECTORS, logger=logger)
                logger.info(f"ASIN {asin} - 총 리뷰 개수: {review_cnt}")
                
                await asyncio.sleep(random.uniform(PAGE_DELAY*0.7, PAGE_DELAY*1.3))
                await page.evaluate(f"window.scrollBy(0, {SCROLL_INCREMENT});")
                await asyncio.sleep(SCROLL_DELAY)
            else:
                next_btn = await extract_next_page_btn(page, REVIEW_NEXT_PAGE_SELECTORS, logger=logger)
                if next_btn:
                    await next_btn.click()
                    await timer.increment_requests()
                    logger.info(f"[크롤링 요청] ASIN {asin} - {page_num}번째 리뷰 페이지(Next) 요청. 현재 총 요청 수: {timer.data['total_requests']}")
                    await asyncio.sleep(random.uniform(PAGE_DELAY*0.7, PAGE_DELAY*1.3))
                else:
                    break
            
            try:
                await page.wait_for_selector("[data-hook='review']", timeout=WAIT_TIME*1000)
            except Exception:
                if page_num == 1:
                    logger.warning(f"ASIN {asin} - 리뷰 페이지에서 리뷰 블록을 찾지 못함. 제품 존재 여부 확인 시작.")
                    product_url = f"{AMAZON_SITE}/dp/{asin}"
                    response = await page.goto(product_url)
                    await timer.increment_requests()
                    logger.info(f"ASIN {asin} - 제품 존재 여부 확인 페이지 요청. 현재 총 요청 수: {timer.data['total_requests']}")

                    if response and response.status == 404:
                        failed_reason = FAILURE_MSG_NO_PRODUCT
                        failure_type = FAILURE_TYPE_PRODUCT_NO_EXIST
                    else:
                        failed_reason = FAILURE_MSG_NO_REVIEWS
                        failure_type = FAILURE_TYPE_NO_REVIEWS
                    
                    logger.info(f"[FAILED_LIST] ASIN {asin} - {failure_type} 유형의 실패가 발생했습니다. (사유: {failed_reason})")
                    await context.close()
                    return [], failed_reason, failure_type
                else:
                    logger.info(f"ASIN {asin} - 페이지 {page_num}에서 더 이상 리뷰 블록을 찾지 못해 크롤링을 종료합니다.")
                    break

            review_blocks = await extract_review_blocks(page, REVIEW_BLOCK_SELECTORS, logger=logger)
            logger.info(f"ASIN {asin} - Page {page_num} - 리뷰 {len(review_blocks)}개 추출")
            for review in review_blocks:
                try:
                    title = await extract_review_title(review, REVIEW_TITLE_SELECTORS, logger=logger)
                    review_url = await extract_review_url(review, REVIEW_TITLE_LINK_SELECTORS, AMAZON_SITE, logger=logger)
                    content = await extract_review_content(review, REVIEW_CONTENT_SELECTORS, logger=logger)
                    star = await extract_review_star(review, REVIEW_STAR_SELECTORS, as_int=True, logger=logger)
                    writer_nm = await extract_writer_name(review, REVIEW_WRITER_SELECTORS, logger=logger)
                    write_dt = await extract_write_dt(review, REVIEW_DATE_SELECTORS, logger=logger)
                    option = await extract_option(review, REVIEW_OPTION_SELECTORS, REVIEW_OPTION_EXCLUDE_KEYWORDS, logger=logger)
                    is_verified = await extract_is_verified(review, REVIEW_VERIFIED_SELECTORS, logger=logger)
                    helpful_text = await extract_first_text_by_selectors(review, REVIEW_HELPFUL_SELECTORS, logger=logger)
                    helpful = parse_helpful(helpful_text)
                    now = datetime.now()
                    crawl_date = now.strftime("%Y-%m-%d")
                    crawl_datetime = now.strftime("%Y-%m-%d %H:%M:%S")
                    # group_id 결정 로직
                    if not option:
                        group_id = asin
                    else:
                        group_id = await extract_group_id(review, REVIEW_OPTION_SELECTORS, GROUP_ID_EXCLUDE_KEYWORDS, logger=logger)
                        if not group_id:
                            group_id = asin
                    review_data = {
                        "seq": 0,
                        "product_seq": 0,
                        "division": "",
                        "flash_memory_size": "",
                        "crawl_date": crawl_date,
                        "crawl_datetime": crawl_datetime,
                        "group_id": group_id,
                        "review_cnt": review_cnt,
                        "title": title,
                        "content": content,
                        "review_url": review_url,
                        "star": star,
                        "writer_nm": writer_nm,
                        "write_dt": write_dt,
                        "option": option,
                        "is_verified": is_verified,
                        "helpful": helpful,
                        "sentiment": "",
                        "rel_words": [
                            {"category": "", "rel_word": ""},
                            {"category": "", "rel_word": ""}
                        ],
                        "groups": [
                            {
                                "large_group_nm": "",
                                "large_group_cd": 0,
                                "middle_group_nm": "",
                                "middle_group_cd": 0,
                                "small_group_nm": "",
                                "small_group_cd": 0,
                                "sentiments": [
                                    {"seq": 0, "type": "", "word": ""},
                                    {"seq": 0, "type": "", "word": ""}
                                ]
                            }
                        ],
                        "rival": [
                            {
                                "brand_name": "",
                                "item_model_number": "",
                                "count": ""
                            },
                            {
                                "brand_name": "",
                                "item_model_number": "",
                                "count": ""
                            }
                        ]
                    }
                    reviews.append(review_data)
                except Exception as e:
                    logger.error(f"ASIN {asin} 리뷰 데이터 추출 중 오류: {e}")
                    failed_reason = FAILURE_MSG_CRAWLING_ERROR
                    failure_type = FAILURE_TYPE_CRAWLING_ERROR
                    logger.info(f"[FAILED_LIST] ASIN {asin} - {failure_type} 유형의 실패가 발생했습니다. (사유: {str(e)})")
                    await context.close()
                    return [], failed_reason, failure_type
            page_num += 1
    except Exception as e:
        failed_reason = str(e)
        failure_type = FAILURE_TYPE_OTHER
        logger.info(f"[FAILED_LIST] ASIN {asin} - {failure_type} 유형의 실패가 발생했습니다. (사유: {failed_reason})")
        await context.close()
        return [], failed_reason, failure_type
    await context.close()
    return reviews, None, None

async def crawl_reviews_for_asin_list_playwright(
    selenium_cookies, asin_list, timer,
    max_pages=MAX_PAGES, headless=True, max_concurrent_contexts=5, logger=None
):
    if logger is None:
        logger = logging.getLogger()
    all_results = []
    all_failed = []

    completed_count = 0
    total_asins = len(asin_list)
    if total_asins > 0:
        logger.info(f"총 {total_asins}개의 ASIN에 대한 크롤링을 시작합니다.")
    else:
        logger.info("크롤링할 ASIN이 없습니다.")
        return [], []

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=headless)
        sem = asyncio.Semaphore(max_concurrent_contexts)  # 동시에 지정된 개수만큼 context 허용
        async def crawl_one(meta):
            asin = meta.get("ASIN")
            if not asin:
                return None, None
            logger.info(f"ASIN: {asin} 크롤링 시작")
            async with sem:
                reviews, fail_reason, failure_type = await crawl_reviews_for_asin_context(browser, selenium_cookies, asin, meta, timer, max_pages, logger=logger)
                
                if fail_reason:
                    failed_info = {
                        "ASIN": asin,
                        "error": fail_reason,
                        "failure_type": failure_type,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    # 요구사항: 실패한 ASIN에 대해서도 비어있는 결과 생성
                    empty_result = {
                        **meta,
                        "remain_count": 0,
                        "has_next": 0,
                        "total_count": 0,
                        "result": [],
                        "crawl_review_cnt": 0
                    }
                    return empty_result, failed_info
                
                result = {
                    **meta,
                    "remain_count": 0,
                    "has_next": 0,
                    "total_count": 0,
                    "result": reviews,
                    "crawl_review_cnt": len(reviews)
                }
                return result, None

        tasks = [crawl_one(meta) for meta in asin_list]
        
        for f in asyncio.as_completed(tasks):
            result, failed_info = await f
            
            completed_count += 1
            progress = (completed_count / total_asins) * 100
            
            current_asin = ""
            if result:
                current_asin = result.get("ASIN", "")
            if not current_asin and failed_info:
                current_asin = failed_info.get("ASIN", "")

            logger.info(f"진행률 {completed_count}/{total_asins} ({progress:.2f}%) - ASIN: {current_asin} 처리 완료. (현재 총 요청 수: {timer.data['total_requests']})")

            if result:
                all_results.append(result)
            if failed_info:
                all_failed.append(failed_info)

        await browser.close()

    return all_results, all_failed 