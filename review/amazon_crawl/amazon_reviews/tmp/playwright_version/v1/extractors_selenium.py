import re
from selenium.webdriver.common.by import By
from logger import logger
from config import REVIEW_STAR_SELECTORS

def strip_html_tags(text):
    if not text:
        return ""
    clean = re.sub('<.*?>', '', text)
    logger.debug(f"[Selenium 추출][strip_html_tags] HTML 태그 제거 결과: {clean}")
    return clean.strip()

def extract_with_selectors(sel_obj, selectors):
    logger.debug(f"[Selenium 추출][extract_with_selectors] selectors: {selectors}")
    try:
        for sel in selectors:
            if isinstance(sel, tuple) and len(sel) == 2:
                sel_type, sel_value = sel
                if sel_type == 'css':
                    elems = sel_obj.find_elements(By.CSS_SELECTOR, sel_value)
                elif sel_type == 'xpath':
                    elems = sel_obj.find_elements(By.XPATH, sel_value)
                else:
                    continue
            else:
                elems = sel_obj.find_elements(By.CSS_SELECTOR, sel)
            for elem in elems:
                val = elem.text
                if val:
                    logger.debug(f"[Selenium 추출][extract_with_selectors] 추출 성공: {val} (type: {type(val)})")
                    return str(val) if val is not None else ""
        logger.debug("[Selenium 추출][extract_with_selectors] 추출 결과 없음 (type: str)")
        return ""
    except Exception as e:
        logger.error(f"[Selenium 추출][extract_with_selectors] 오류 발생 - {e}, selectors={selectors}")
        return ""

def extract_attr_with_selectors(sel_obj, selectors, attr):
    logger.debug(f"[Selenium 추출][extract_attr_with_selectors] selectors: {selectors}, attr: {attr}")
    for sel_type, sel_value in selectors:
        if sel_type == "css":
            elems = sel_obj.find_elements(By.CSS_SELECTOR, sel_value)
        elif sel_type == "xpath":
            elems = sel_obj.find_elements(By.XPATH, sel_value)
        else:
            continue
        for elem in elems:
            val = elem.get_attribute(attr)
            if val:
                logger.debug(f"[Selenium 추출][extract_attr_with_selectors] 추출 성공: {val}")
                return val.strip()
    logger.debug(f"[Selenium 추출][extract_attr_with_selectors] 추출 실패")
    return ""

def extract_star(star_text):
    logger.debug(f"[Selenium 추출][extract_star] 입력: {star_text}")
    if not star_text:
        return ""
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)", str(star_text))
    if match:
        logger.debug(f"[Selenium 추출][extract_star] 추출 성공: {match.group(1)}")
        return match.group(1)
    logger.debug(f"[Selenium 추출][extract_star] 추출 실패")
    return ""

def extract_writer_name(review, REVIEW_WRITER_SELECTORS):
    logger.debug(f"[Selenium 추출][extract_writer_name] selectors: {REVIEW_WRITER_SELECTORS}")
    try:
        for sel_type, sel_value in REVIEW_WRITER_SELECTORS:
            if sel_type == "css":
                elems = review.find_elements(By.CSS_SELECTOR, sel_value)
            elif sel_type == "xpath":
                elems = review.find_elements(By.XPATH, sel_value)
            else:
                continue
            for elem in elems:
                val = elem.text
                if val:
                    logger.debug(f"[Selenium 추출][extract_writer_name] 추출 성공: {val} (type: {type(val)})")
                    return str(val).strip() if val is not None else ""
        logger.debug("[Selenium 추출][extract_writer_name] 추출 결과 없음 (type: str)")
        return ""
    except Exception as e:
        logger.error(f"[Selenium 추출][extract_writer_name] 오류 발생 - {e}, selectors={REVIEW_WRITER_SELECTORS}")
        return ""

# def extract_review_count(driver, REVIEW_COUNT_SELECTORS):
#     for sel_type, sel_value in REVIEW_COUNT_SELECTORS:
#         if sel_type == "css":
#             elems = driver.find_elements(By.CSS_SELECTOR, sel_value)
#         elif sel_type == "xpath":
#             elems = driver.find_elements(By.XPATH, sel_value)
#         else:
#             continue
#         for elem in elems:
#             text = elem.text
#             if text:
#                 match = re.search(r"([0-9,]+)\s+customer reviews", text)
#                 if match:
#                     return int(match.group(1).replace(",", ""))
#                 if "No customer reviews" in text:
#                     return 0
#     return 0
def extract_review_count(driver, REVIEW_COUNT_SELECTORS):
    logger.debug(f"[Selenium 추출][extract_review_count] selectors: {REVIEW_COUNT_SELECTORS}")
    for sel_type, sel_value in REVIEW_COUNT_SELECTORS:
        if sel_type == "css":
            elems = driver.find_elements(By.CSS_SELECTOR, sel_value)
        elif sel_type == "xpath":
            elems = driver.find_elements(By.XPATH, sel_value)
        else:
            continue
        for elem in elems:
            text = elem.text
            if text:
                # 1. "No customer reviews" 우선 처리
                if "No customer reviews" in text:
                    logger.debug(f"[Selenium 추출][extract_review_count] 리뷰 없음 감지")
                    return 0
                # 2. "N customer review" 또는 "N customer reviews" 모두 매칭
                match = re.search(r"([0-9,]+)\s+customer review(s)?", text)
                if match:
                    logger.debug(f"[Selenium 추출][extract_review_count] 추출 성공: {match.group(1)}")
                    return int(match.group(1).replace(",", ""))
    logger.debug(f"[Selenium 추출][extract_review_count] 추출 실패")
    return 0


def extract_first_text_by_selectors(sel_obj, selectors):
    logger.debug(f"[Selenium 추출][extract_first_text_by_selectors] selectors: {selectors}")
    for sel_type, sel_value in selectors:
        if sel_type == "css":
            elems = sel_obj.find_elements(By.CSS_SELECTOR, sel_value)
        elif sel_type == "xpath":
            elems = sel_obj.find_elements(By.XPATH, sel_value)
        else:
            continue
        for elem in elems:
            val = elem.text
            if val:
                logger.debug(f"[Selenium 추출][extract_first_text_by_selectors] 추출 성공: {val}")
                return str(val).strip() if val is not None else ""
    logger.debug(f"[Selenium 추출][extract_first_text_by_selectors] 추출 실패")
    return ""

def parse_helpful(text):
    logger.debug(f"[Selenium 추출][parse_helpful] 입력: {text}")
    if not text:
        return 0
    text = str(text).strip()
    if "One person" in text:
        logger.debug(f"[Selenium 추출][parse_helpful] 1명 추출")
        return 1
    m = re.search(r"(\d+)", text.replace(",", ""))
    if m:
        logger.debug(f"[Selenium 추출][parse_helpful] 추출 성공: {m.group(1)}")
        return int(m.group(1))
    logger.debug(f"[Selenium 추출][parse_helpful] 추출 실패")
    return 0

def extract_review_title(review, REVIEW_TITLE_SELECTORS):
    logger.debug(f"[Selenium 추출][extract_review_title] selectors: {REVIEW_TITLE_SELECTORS}")
    try:
        for sel_type, sel_value in REVIEW_TITLE_SELECTORS:
            if sel_type == "css":
                elems = review.find_elements(By.CSS_SELECTOR, sel_value)
            elif sel_type == "xpath":
                elems = review.find_elements(By.XPATH, sel_value)
            else:
                continue
            for elem in elems:
                class_attr = elem.get_attribute("class") or ""
                if "a-icon-alt" in class_attr or "a-letter-space" in class_attr:
                    continue
                text = elem.text
                if text and text.strip():
                    logger.debug(f"[Selenium 추출][extract_review_title] 추출 성공: {text} (type: {type(text)})")
                    return str(text).strip() if text is not None else ""
        # fallback: a[data-hook='review-title'] 내부의 class 없는 span
        a_title = review.find_elements(By.CSS_SELECTOR, "a[data-hook='review-title']")
        if a_title:
            spans = a_title[0].find_elements(By.CSS_SELECTOR, "span")
            for span in spans:
                class_attr = span.get_attribute("class") or ""
                if not class_attr or "cr-original-review-content" in class_attr:
                    text = span.text
                    if text and text.strip():
                        logger.debug(f"[Selenium 추출][extract_review_title] fallback 추출 성공: {text} (type: {type(text)})")
                        return str(text).strip() if text is not None else ""
        logger.debug("[Selenium 추출][extract_review_title] 추출 결과 없음 (type: str)")
        return ""
    except Exception as e:
        logger.error(f"[Selenium 추출][extract_review_title] 오류 발생 - {e}, selectors={REVIEW_TITLE_SELECTORS}")
        return ""

def extract_review_content(review, REVIEW_CONTENT_SELECTORS):
    logger.debug(f"[Selenium 추출][extract_review_content] selectors: {REVIEW_CONTENT_SELECTORS}")
    try:
        for sel_type, sel_value in REVIEW_CONTENT_SELECTORS:
            if sel_type == "css":
                elems = review.find_elements(By.CSS_SELECTOR, sel_value)
            elif sel_type == "xpath":
                elems = review.find_elements(By.XPATH, sel_value)
            else:
                continue
            for elem in elems:
                val = elem.text
                if val:
                    logger.debug(f"[Selenium 추출][extract_review_content] 추출 성공: {val} (type: {type(val)})")
                    return str(val).strip() if val is not None else ""
        logger.debug("[Selenium 추출][extract_review_content] 추출 결과 없음 (type: str)")
        return ""
    except Exception as e:
        logger.error(f"[Selenium 추출][extract_review_content] 오류 발생 - {e}, selectors={REVIEW_CONTENT_SELECTORS}")
        return ""

def extract_review_url(sel_obj, selectors, base_url):
    logger.debug(f"[Selenium 추출][extract_review_url] selectors: {selectors}, base_url: {base_url}")
    url = extract_attr_with_selectors(sel_obj, selectors, "href")
    if url:
        url = str(url)
        if url.startswith("http"):
            logger.debug(f"[Selenium 추출][extract_review_url] 절대 URL 반환: {url}")
            return url
        else:
            logger.debug(f"[Selenium 추출][extract_review_url] 상대 URL 반환: {base_url + url}")
            return base_url + url
    logger.debug(f"[Selenium 추출][extract_review_url] 링크 없음")
    return ""

# def extract_all_texts_by_selectors(sel_obj, selectors, exclude=None):
#     exclude = exclude or []
#     for sel_type, sel_value in selectors:
#         if sel_type == "css":
#             elems = sel_obj.find_elements(By.CSS_SELECTOR, sel_value)
#         elif sel_type == "xpath":
#             elems = sel_obj.find_elements(By.XPATH, sel_value)
#         else:
#             continue
#         texts = []
#         for elem in elems:
#             val = elem.text
#             if val and all(ex not in val for ex in exclude):
#                 texts.append(val.strip())
#         if texts:
#             return texts
#     return []

def extract_option(review, REVIEW_OPTION_SELECTORS, REVIEW_OPTION_EXCLUDE_KEYWORDS):
    logger.debug(f"[Selenium 추출][extract_option] selectors: {REVIEW_OPTION_SELECTORS}")
    try:
        import re
        option_texts = []
        for selector in REVIEW_OPTION_SELECTORS:
            elems = review.find_elements(By.XPATH, selector)
            for elem in elems:
                try:
                    html = elem.get_attribute("innerHTML")
                    if html:
                        # 모든 <i ...>...</i> 태그를 공백으로 치환
                        html = re.sub(r'<i[^>]*>.*?</i>', ' ', html)
                        # '|'로 split 후 각 옵션을 정제
                        split_options = [t.strip() for t in html.split('|') if t.strip()]
                        for text in split_options:
                            if not any(ex_kw in text for ex_kw in REVIEW_OPTION_EXCLUDE_KEYWORDS):
                                option_texts.append(text)
                    else:
                        text = elem.get_attribute("innerText")
                        if not text:
                            text = elem.text
                        if text:
                            text = text.strip()
                            if not any(ex_kw in text for ex_kw in REVIEW_OPTION_EXCLUDE_KEYWORDS):
                                option_texts.append(text)
                except Exception:
                    text = elem.text
                    if text:
                        text = text.strip()
                        if not any(ex_kw in text for ex_kw in REVIEW_OPTION_EXCLUDE_KEYWORDS):
                            option_texts.append(text)
        # 중복 제거 및 순서 유지
        option_texts = list(dict.fromkeys(option_texts))
        # 옵션 텍스트 내 연속 공백 정제
        option_texts = [" ".join(t.split()) for t in option_texts]
        logger.debug(f"[Selenium 추출][extract_option] 추출 성공: {option_texts}")
        return " ".join(option_texts)
    except Exception as e:
        logger.error(f"[Selenium 추출][extract_option] 오류 발생 - {e}, selectors={REVIEW_OPTION_SELECTORS}")
        return ""

def extract_is_verified(review, REVIEW_VERIFIED_SELECTORS):
    logger.debug(f"[Selenium 추출][extract_is_verified] selectors: {REVIEW_VERIFIED_SELECTORS}")
    try:
        for selector in REVIEW_VERIFIED_SELECTORS:
            elems = review.find_elements(By.XPATH, selector)
            if elems:
                logger.debug(f"[Selenium 추출][extract_is_verified] 추출 성공: True (type: bool)")
                return True
        logger.debug(f"[Selenium 추출][extract_is_verified] 추출 실패: False (type: bool)")
        return False
    except Exception as e:
        logger.error(f"[Selenium 추출][extract_is_verified] 오류 발생 - {e}, selectors={REVIEW_VERIFIED_SELECTORS}")
        return False

def extract_rating_value(rating_text):
    logger.debug(f"[Selenium 추출][extract_rating_value] 입력: {rating_text}")
    import re
    if not rating_text or rating_text == 'N/A':
        return 0.0
    match = re.search(r"(\d+\.?\d*)", rating_text)
    if match:
        logger.debug(f"[Selenium 추출][extract_rating_value] 추출 성공: {match.group(1)}")
        return float(match.group(1))
    logger.debug(f"[Selenium 추출][extract_rating_value] 추출 실패")
    return 0.0

def parse_rating(text):
    logger.debug(f"[Selenium 추출][parse_rating] 입력: {text}")
    if not text:
        return 0.0
    m = re.search(r"([1-5](?:\.\d)?)\s*out of", text)
    if m:
        logger.debug(f"[Selenium 추출][parse_rating] 추출 성공: {m.group(1)}")
        return float(m.group(1))
    m = re.search(r"([1-5](?:\.\d)?)", text)
    if m:
        logger.debug(f"[Selenium 추출][parse_rating] 추출 성공: {m.group(1)}")
        return float(m.group(1))
    logger.debug(f"[Selenium 추출][parse_rating] 추출 실패")
    return 0.0

def extract_review_star(driver, review, as_int=False):
    logger.debug(f"[Selenium 추출][extract_review_star] as_int={as_int}")
    for sel_type, sel_value in REVIEW_STAR_SELECTORS:
        try:
            if sel_type == 'css':
                elems = review.find_elements(By.CSS_SELECTOR, sel_value)
            elif sel_type == 'xpath':
                elems = review.find_elements(By.XPATH, sel_value)
            else:
                continue
            for elem in elems:
                rating_text = elem.get_attribute('aria-label')
                if not rating_text:
                    try:
                        rating_text = elem.get_attribute('innerText')
                    except Exception:
                        rating_text = elem.text
                if rating_text:
                    star = parse_rating(rating_text)
                    logger.debug(f"[Selenium 추출][extract_review_star] selector={sel_type}:{sel_value}, text={rating_text}, star={star}")
                    if star > 0:
                        return int(round(star)) if as_int else star
        except Exception as e:
            logger.debug(f"[Selenium 추출][extract_review_star] selector={sel_type}:{sel_value} 오류: {e}")
    try:
        rating_script = '''
        var sel = [
            "i[data-hook='review-star-rating'] span.a-icon-alt",
            "i[data-hook='cmps-review-star-rating'] span.a-icon-alt",
            "i.a-icon-star span.a-icon-alt",
            "span.a-icon-alt"
        ];
        for (var i = 0; i < sel.length; i++) {
            var el = arguments[0].querySelector(sel[i]);
            if (el && el.innerText) return el.innerText;
        }
        var i_els = arguments[0].querySelectorAll('i[data-hook], i.a-icon-star');
        for (var j = 0; j < i_els.length; j++) {
            if (i_els[j].getAttribute('aria-label')) return i_els[j].getAttribute('aria-label');
        }
        return '';
        '''
        rating_text = driver.execute_script(rating_script, review)
        star = parse_rating(rating_text)
        logger.debug(f"[Selenium 추출][extract_review_star] JS fallback, text={rating_text}, star={star}")
        if star > 0:
            return int(round(star)) if as_int else star
    except Exception as e:
        logger.debug(f"[Selenium 추출][extract_review_star] JS fallback 오류: {e}")
    logger.warning("[Selenium 추출][extract_review_star] 평점 추출 실패, 0 반환")
    return 0 if as_int else 0.0
