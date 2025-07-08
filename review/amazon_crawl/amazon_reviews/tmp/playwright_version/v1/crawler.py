"""
아마존 리뷰 크롤링 (Playwright Only)
- Selenium에서 로그인 후 쿠키를 Playwright로 전달받아 세션 유지
- 여러 ASIN을 비동기 병렬로 크롤링
- config.py의 셀렉터를 그대로 사용
"""
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
from logger import logger
from utils import save_results_to_json, save_failed_asin
from config import (
    AMAZON_SITE, FAILURE_TYPE_CRAWLING_ERROR, REVIEW_BLOCK_SELECTORS, REVIEW_COUNT_SELECTORS, REVIEW_TITLE_SELECTORS, REVIEW_TITLE_LINK_SELECTORS,
    REVIEW_CONTENT_SELECTORS, REVIEW_STAR_SELECTORS, REVIEW_WRITER_SELECTORS, REVIEW_DATE_SELECTORS,
    REVIEW_OPTION_SELECTORS, REVIEW_OPTION_EXCLUDE_KEYWORDS, REVIEW_VERIFIED_SELECTORS, REVIEW_HELPFUL_SELECTORS,
    REVIEW_NEXT_PAGE_SELECTORS, MAX_PAGES, FAILURE_TYPE_NO_REVIEWS, FAILURE_TYPE_PRODUCT_NO_EXIST, FAILURE_TYPE_OTHER,
    FAILURE_MSG_NO_REVIEWS, FAILURE_MSG_NO_PRODUCT, FAILURE_MSG_OTHER, FAILED_ASIN_PATH,
    PAGE_DELAY, SCROLL_DELAY, SCROLL_INCREMENT, WAIT_TIME, RESULTS_PATH
)
import random
import time
import re
from dateutil import parser as date_parser

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

def strip_html_tags(text):
    if not text:
        return ""
    clean = re.sub('<.*?>', '', text)
    return clean.strip()

async def extract_text(element, selectors):
    for sel_type, sel_value in selectors:
        try:
            if sel_type == "css":
                el = await element.query_selector(sel_value)
            elif sel_type == "xpath":
                el = (await element.query_selector_all(f"xpath={sel_value}"))[0] if (await element.query_selector_all(f"xpath={sel_value}")) else None
            else:
                continue
            if el:
                text = await el.inner_text()
                if text:
                    return text.strip()
        except Exception:
            continue
    return ""

async def extract_review_count(page, selectors):
    for sel_type, sel_value in selectors:
        try:
            if sel_type == "css":
                el = await page.query_selector(sel_value)
            elif sel_type == "xpath":
                el = await page.query_selector(f"xpath={sel_value}")
            else:
                continue
            if el:
                text = await el.inner_text()
                if text:
                    if "No customer reviews" in text:
                        return 0
                    m = re.search(r"([0-9,]+)\s+customer review(s)?", text)
                    if m:
                        return int(m.group(1).replace(",", ""))
        except Exception:
            continue
    return 0

async def extract_review_title(review, selectors):
    for sel_type, sel_value in selectors:
        try:
            if sel_type == "css":
                el = await review.query_selector(sel_value)
            elif sel_type == "xpath":
                el = await review.query_selector(f"xpath={sel_value}")
            else:
                continue
            if el:
                class_attr = (await el.get_attribute("class")) or ""
                if "a-icon-alt" in class_attr or "a-letter-space" in class_attr:
                    continue
                text = await el.inner_text()
                if text and text.strip():
                    return text.strip()
        except Exception:
            continue
    # fallback: a[data-hook='review-title'] 내부의 class 없는 span
    a_title = await review.query_selector("a[data-hook='review-title']")
    if a_title:
        spans = await a_title.query_selector_all("span")
        for span in spans:
            class_attr = (await span.get_attribute("class")) or ""
            if not class_attr or "cr-original-review-content" in class_attr:
                text = await span.inner_text()
                if text and text.strip():
                    return text.strip()
    return ""

async def extract_review_content(review, selectors):
    for sel_type, sel_value in selectors:
        try:
            if sel_type == "css":
                el = await review.query_selector(sel_value)
            elif sel_type == "xpath":
                el = await review.query_selector(f"xpath={sel_value}")
            else:
                continue
            if el:
                text = await el.inner_text()
                if text:
                    return text.strip()
        except Exception:
            continue
    return ""

async def extract_review_url(review, selectors, base_url):
    for sel_type, sel_value in selectors:
        try:
            if sel_type == "css":
                el = await review.query_selector(sel_value)
            elif sel_type == "xpath":
                el = await review.query_selector(f"xpath={sel_value}")
            else:
                continue
            if el:
                url = await el.get_attribute("href")
                if url:
                    url = str(url)
                    if url.startswith("http"):
                        return url
                    else:
                        return base_url + url
        except Exception:
            continue
    return ""

async def extract_writer_name(review, selectors):
    for sel_type, sel_value in selectors:
        try:
            if sel_type == "css":
                el = await review.query_selector(sel_value)
            elif sel_type == "xpath":
                el = await review.query_selector(f"xpath={sel_value}")
            else:
                continue
            if el:
                text = await el.inner_text()
                if text:
                    return text.strip()
        except Exception:
            continue
    return ""

async def extract_option(review, selectors, exclude_keywords):
    option_texts = []
    for selector in selectors:
        try:
            els = await review.query_selector_all(f"xpath={selector}")
            for el in els:
                html = await el.get_attribute("innerHTML")
                if html:
                    html = re.sub(r'<i[^>]*>.*?</i>', ' ', html)
                    split_options = [t.strip() for t in html.split('|') if t.strip()]
                    for text in split_options:
                        if not any(ex_kw in text for ex_kw in exclude_keywords):
                            option_texts.append(text)
                else:
                    text = await el.inner_text()
                    if text:
                        text = text.strip()
                        if not any(ex_kw in text for ex_kw in exclude_keywords):
                            option_texts.append(text)
        except Exception:
            continue
    option_texts = list(dict.fromkeys(option_texts))
    option_texts = [" ".join(t.split()) for t in option_texts]
    return " ".join(option_texts)

async def extract_is_verified(review, selectors):
    for selector in selectors:
        try:
            els = await review.query_selector_all(f"xpath={selector}")
            if els and len(els) > 0:
                return True
        except Exception:
            continue
    return False

async def extract_first_text_by_selectors(review, selectors):
    for sel_type, sel_value in selectors:
        try:
            if sel_type == "css":
                el = await review.query_selector(sel_value)
            elif sel_type == "xpath":
                el = await review.query_selector(f"xpath={sel_value}")
            else:
                continue
            if el:
                text = await el.inner_text()
                if text:
                    return text.strip()
        except Exception:
            continue
    return ""

def parse_helpful(text):
    if not text:
        return 0
    text = str(text).strip()
    if "One person" in text:
        return 1
    m = re.search(r"(\d+)", text.replace(",", ""))
    if m:
        return int(m.group(1))
    return 0

def parse_write_dt(text):
    try:
        if not text:
            return ""
        if "on " in text:
            date_str = text.split("on ")[-1].strip()
        else:
            date_str = text.strip()
        dt = date_parser.parse(date_str)
        return dt.strftime('%Y-%m-%d')
    except Exception:
        return text

def parse_star(text):
    try:
        if not text:
            return 0.0
        m = re.search(r"([1-5](?:\.\d)?)", text)
        if m:
            return float(m.group(1))
    except Exception:
        pass
    return 0.0

async def extract_review_blocks(page, selectors):
    for sel_type, sel_value in selectors:
        try:
            if sel_type == "css":
                blocks = await page.query_selector_all(sel_value)
            elif sel_type == "xpath":
                blocks = await page.query_selector_all(f"xpath={sel_value}")
            else:
                continue
            if blocks:
                return blocks
        except Exception:
            continue
    return []

def parse_review_url(url, base_url):
    if not url:
        return ""
    url = str(url)
    if url.startswith("http"):
        return url
    return base_url + url

def parse_option(option_text):
    if not option_text:
        return ""
    return " ".join(option_text.split())

def parse_is_verified(text):
    if not text:
        return False
    return text.strip().lower() == "verified purchase"

async def crawl_reviews_for_asin_context(browser, selenium_cookies, asin, meta_info, max_pages=MAX_PAGES, failed_asins=None):
    if failed_asins is None:
        failed_asins = []
    reviews = []
    failed_reason = None
    failure_type = None
    base_url = f"{AMAZON_SITE}/product-reviews/{asin}"
    page_num = 1
    context = await browser.new_context()
    cookies = selenium_cookies_to_playwright(selenium_cookies)
    await context.add_cookies(cookies)
    page = await context.new_page()
    try:
        while page_num <= max_pages:
            if page_num == 1:
                review_page_url = f"{base_url}/ref=cm_cr_arp_d_viewopt_srt?ie=UTF8&reviewerType=all_reviews&sortBy=recent&pageNumber=1"
                await page.goto(review_page_url)
                await asyncio.sleep(random.uniform(PAGE_DELAY*0.7, PAGE_DELAY*1.3))
                await page.evaluate(f"window.scrollBy(0, {SCROLL_INCREMENT});")
                await asyncio.sleep(SCROLL_DELAY)
            else:
                next_btn = None
                for sel_type, sel_value in REVIEW_NEXT_PAGE_SELECTORS:
                    try:
                        if sel_type == "css":
                            next_btn = await page.query_selector(sel_value)
                        elif sel_type == "xpath":
                            btns = await page.query_selector_all(f"xpath={sel_value}")
                            next_btn = btns[0] if btns else None
                        if next_btn:
                            break
                    except Exception:
                        continue
                if next_btn:
                    await next_btn.click()
                    await asyncio.sleep(random.uniform(PAGE_DELAY*0.7, PAGE_DELAY*1.3))
                else:
                    break
            await page.wait_for_selector("[data-hook='review']", timeout=WAIT_TIME*1000)
            review_blocks = await extract_review_blocks(page, REVIEW_BLOCK_SELECTORS)
            logger.info(f"[크롤링] ASIN {asin} - Page {page_num} - 리뷰 {len(review_blocks)}개 추출")
            for review in review_blocks:
                try:
                    title = await extract_text(review, REVIEW_TITLE_SELECTORS)
                    review_url_raw = await extract_text(review, REVIEW_TITLE_LINK_SELECTORS)
                    review_url = parse_review_url(review_url_raw, base_url)
                    content = await extract_text(review, REVIEW_CONTENT_SELECTORS)
                    star_raw = await extract_text(review, REVIEW_STAR_SELECTORS)
                    star = parse_star(star_raw)
                    writer_nm = await extract_text(review, REVIEW_WRITER_SELECTORS)
                    write_dt_raw = await extract_text(review, REVIEW_DATE_SELECTORS)
                    write_dt = parse_write_dt(write_dt_raw)
                    option_raw = await extract_text(review, [("xpath", sel) for sel in REVIEW_OPTION_SELECTORS])
                    option = parse_option(option_raw)
                    is_verified_raw = await extract_text(review, [("xpath", sel) for sel in REVIEW_VERIFIED_SELECTORS])
                    is_verified = parse_is_verified(is_verified_raw)
                    helpful_raw = await extract_text(review, REVIEW_HELPFUL_SELECTORS)
                    helpful = parse_helpful(helpful_raw)
                    now = datetime.now()
                    crawl_date = now.strftime("%Y-%m-%d")
                    crawl_datetime = now.strftime("%Y-%m-%d %H:%M:%S")
                    review_data = {
                        "seq": 0,
                        "product_seq": 0,
                        "division": "",
                        "flash_memory_size": "",
                        "crawl_date": crawl_date,
                        "crawl_datetime": crawl_datetime,
                        "group_id": asin,
                        "review_cnt": 0,
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
                    logger.error(f"[크롤링] ASIN {asin} 리뷰 크롤링 중 오류: {e}")
                    failed_reason = str(e)
                    failure_type = FAILURE_TYPE_CRAWLING_ERROR
                    save_failed_asin(
                        asin=asin,
                        error=failed_reason,
                        failure_type=failure_type,
                        failed_list=failed_asins,
                        output_path=FAILED_ASIN_PATH
                    )
                    await context.close()
                    return [], failed_reason, failure_type
            page_num += 1
    except Exception as e:
        failed_reason = str(e)
        failure_type = FAILURE_TYPE_OTHER
        save_failed_asin(
            asin=asin,
            error=failed_reason,
            failure_type=failure_type,
            failed_list=failed_asins,
            output_path=FAILED_ASIN_PATH
        )
        logger.info(f"[FAILED_LIST] ASIN {asin} - {failure_type} 유형의 실패가 발생했고 Failed_List에 저장했습니다. (사유: {failed_reason})")
        await context.close()
        return [], failed_reason, failure_type
    await context.close()
    return reviews, failed_reason, failure_type

async def crawl_reviews_for_asin_list_playwright(selenium_cookies, asin_list, max_pages=MAX_PAGES, output_filename=None, headless=True, max_concurrent_contexts=5):
    all_results = []
    failed_asins = []
    if output_filename is None:
        now_str = datetime.now().strftime("%Y%m%d%H%M%S")
        output_filename = f"ASIN_REVIEWS_Excel_{now_str}.json"
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=headless)
        sem = asyncio.Semaphore(max_concurrent_contexts)  # 동시에 지정된 개수만큼 context 허용
        async def crawl_one(meta):
            asin = meta.get("ASIN")
            if not asin:
                return None
            logger.info(f"[진행률] ASIN: {asin} 크롤링 시작")
            async with sem:
                reviews, fail_reason, failure_type = await crawl_reviews_for_asin_context(browser, selenium_cookies, asin, meta, max_pages, failed_asins)
                result = {
                    **meta,
                    "remain_count": 0,
                    "has_next": 0,
                    "total_count": 0,
                    "result": reviews,
                    "crawl_review_cnt": len(reviews)
                }
                return result
        tasks = [crawl_one(meta) for meta in asin_list]
        results = await asyncio.gather(*tasks)
        for r in results:
            if r:
                all_results.append(r)
        save_results_to_json(all_results, filename=RESULTS_PATH)
        logger.info(f"[최종 요청수] 총 {len(all_results)}개 ASIN 크롤링 완료")
        await browser.close()
    return all_results, failed_asins 