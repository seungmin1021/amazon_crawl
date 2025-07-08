import re
import logging

async def extract_review_blocks(page, selectors, logger=None):
    if logger is None:
        logger = logging.getLogger()
    for sel_type, sel_value in selectors:
        try:
            if sel_type == "css":
                blocks = await page.query_selector_all(sel_value)
            elif sel_type == "xpath":
                blocks = await page.query_selector_all(f"xpath={sel_value}")
            else:
                continue
            if blocks:
                logger.debug(f"[Playwright 추출][extract_review_blocks] 추출 성공: {len(blocks)}개")
                return blocks
        except Exception as e:
            logger.error(f"[Playwright 추출][extract_review_blocks] 오류 발생 - {e}, selector={sel_type}:{sel_value}")
            continue
    logger.warning(f"[Playwright 추출][extract_review_blocks] 추출 실패")
    return []


async def strip_html_tags(text, logger=None):
    if logger is None:
        logger = logging.getLogger()
    try:
        if not text:
            return ""
        clean = re.sub('<.*?>', '', text)
        logger.debug(f"[Playwright 추출][strip_html_tags] HTML 태그 제거 결과: {clean}")
        return clean.strip()
    except Exception as e:
        logger.error(f"[Playwright 추출][strip_html_tags] 오류 발생 - {e}")
        return ""

async def extract_with_selectors(element, selectors, logger=None):
    if logger is None:
        logger = logging.getLogger()
    try:
        for sel in selectors:
            if isinstance(sel, tuple) and len(sel) == 2:
                sel_type, sel_value = sel
                if sel_type == 'css':
                    elems = await element.query_selector_all(sel_value)
                elif sel_type == 'xpath':
                    elems = await element.query_selector_all(f"xpath={sel_value}")
                else:
                    continue
            else:
                elems = await element.query_selector_all(sel)
            for elem in elems:
                val = await elem.inner_text()
                if val:
                    logger.debug(f"[Playwright 추출][extract_with_selectors] 추출 성공: {val}")
                    return str(val)
        logger.debug("[Playwright 추출][extract_with_selectors] 추출 결과 없음 (type: str)")
        return ""
    except Exception as e:
        logger.error(f"[Playwright 추출][extract_with_selectors] 오류 발생 - {e}, selectors={selectors}")
        return ""

async def extract_attr_with_selectors(element, selectors, attr, logger=None):
    if logger is None:
        logger = logging.getLogger()
    try:
        for sel_type, sel_value in selectors:
            if sel_type == "css":
                elems = await element.query_selector_all(sel_value)
            elif sel_type == "xpath":
                elems = await element.query_selector_all(f"xpath={sel_value}")
            else:
                continue
            for elem in elems:
                val = await elem.get_attribute(attr)
                if val:
                    logger.debug(f"[Playwright 추출][extract_attr_with_selectors] 추출 성공: {val}")
                    return val.strip()
        logger.debug(f"[Playwright 추출][extract_attr_with_selectors] 추출 실패")
        return ""
    except Exception as e:
        logger.error(f"[Playwright 추출][extract_attr_with_selectors] 오류 발생 - {e}, selectors={selectors}, attr={attr}")
        return ""

async def extract_review_title(review, REVIEW_TITLE_SELECTORS, logger=None):
    if logger is None:
        logger = logging.getLogger()
    try:
        for sel_type, sel_value in REVIEW_TITLE_SELECTORS:
            if sel_type == "css":
                elems = await review.query_selector_all(sel_value)
            elif sel_type == "xpath":
                elems = await review.query_selector_all(f"xpath={sel_value}")
            else:
                continue
            for elem in elems:
                class_attr = await elem.get_attribute("class") or ""
                if "a-icon-alt" in class_attr or "a-letter-space" in class_attr:
                    continue
                text = await elem.inner_text()
                if text and text.strip():
                    logger.debug(f"[Playwright 추출][extract_review_title] 추출 성공: {text}")
                    return str(text).strip()
        # fallback: a[data-hook='review-title'] 내부의 class 없는 span
        a_title = await review.query_selector("a[data-hook='review-title']")
        if a_title:
            spans = await a_title.query_selector_all("span")
            for span in spans:
                class_attr = await span.get_attribute("class") or ""
                if not class_attr or "cr-original-review-content" in class_attr:
                    text = await span.inner_text()
                    if text and text.strip():
                        logger.debug(f"[Playwright 추출][extract_review_title] fallback 추출 성공: {text}")
                        return str(text).strip()
        logger.debug("[Playwright 추출][extract_review_title] 추출 결과 없음 (type: str)")
        return ""
    except Exception as e:
        logger.error(f"[Playwright 추출][extract_review_title] 오류 발생 - {e}, selectors={REVIEW_TITLE_SELECTORS}")
        return ""

async def extract_review_content(review, REVIEW_CONTENT_SELECTORS, logger=None):
    if logger is None:
        logger = logging.getLogger()
    
    logger.debug(f"[Playwright 추출][extract_review_content] 실행, Selectors: {REVIEW_CONTENT_SELECTORS}")
    try:
        # 설정 파일에 정의된 selector들을 순회하며 리뷰 본문 컨테이너를 찾습니다.
        for sel_type, sel_value in REVIEW_CONTENT_SELECTORS:
            review_body_el = None
            if sel_type == "css":
                review_body_el = await review.query_selector(sel_value)
            elif sel_type == "xpath":
                review_body_el = await review.query_selector(f"xpath={sel_value}")
            
            # 컨테이너를 찾았다면, 내부의 텍스트를 정제하여 추출합니다.
            if review_body_el:
                logger.debug(f"[Playwright 추출][extract_review_content] 리뷰 본문 컨테이너 찾음 (selector: {sel_type}='{sel_value}')")
                
                # page.evaluate를 사용해 브라우저 단에서 직접 JS 코드를 실행합니다.
                # 이를 통해 비디오 블록 등 불필요한 요소를 제거하고 텍스트를 추출할 수 있습니다.
                content = await review_body_el.evaluate('''
                    (element) => {
                        // 실제 페이지의 DOM을 변경하지 않기 위해 element를 복제해서 사용합니다.
                        const clone = element.cloneNode(true);
                        
                        // 리뷰 내부에 비디오 플레이어 블록(div.video-block)이 있다면 제거합니다.
                        const videoBlock = clone.querySelector('div.video-block');
                        if (videoBlock) {
                            videoBlock.remove();
                        }
                        
                        // '더 보기'로 숨겨진 전체 리뷰 텍스트가 있는지 확인하고, 있다면 그 내용을 반환합니다.
                        const a_expander_content = clone.querySelector('.a-expander-content');
                        if (a_expander_content && a_expander_content.textContent.trim()) {
                            return a_expander_content.textContent.trim();
                        }

                        // 번역된 리뷰의 경우, 원문이 별도의 요소에 담겨 있을 수 있습니다.
                        const originalReviewContent = clone.querySelector('.cr-original-review-content');
                        if (originalReviewContent && originalReviewContent.textContent.trim()){
                            return originalReviewContent.textContent.trim();
                        }

                        // 위 케이스에 해당하지 않으면, 정제된 컨테이너의 전체 텍스트를 반환합니다.
                        // .textContent는 숨겨진 텍스트까지 모두 가져올 수 있어 .innerText보다 효과적입니다.
                        return clone.textContent.trim();
                    }
                ''')

                # 추출된 텍스트가 유효한지 확인합니다.
                if content and content.strip():
                    clean_content = ' '.join(content.strip().split())
                    logger.debug(f"[Playwright 추출][extract_review_content] 추출 성공: {clean_content}")
                    return clean_content
                
        logger.warning("[Playwright 추출][extract_review_content] 모든 selector로 리뷰 본문을 추출하지 못했습니다.")
        return ""
    except Exception as e:
        logger.error(f"[Playwright 추출][extract_review_content] 오류 발생 - {e}")
        return ""

async def extract_review_url(review, REVIEW_TITLE_LINK_SELECTORS, base_url, logger=None):
    if logger is None:
        logger = logging.getLogger()
    try:
        url = await extract_attr_with_selectors(review, REVIEW_TITLE_LINK_SELECTORS, "href", logger)
        if url:
            url = str(url)
            if url.startswith("http"):
                logger.debug(f"[Playwright 추출][extract_review_url] 절대 URL 반환: {url}")
                return url
            else:
                logger.debug(f"[Playwright 추출][extract_review_url] 상대 URL 반환: {base_url + url}")
                return base_url + url
        logger.debug(f"[Playwright 추출][extract_review_url] 링크 없음")
        return ""
    except Exception as e:
        logger.error(f"[Playwright 추출][extract_review_url] 오류 발생 - {e}, selectors={REVIEW_TITLE_LINK_SELECTORS}")
        return ""

async def extract_writer_name(review, REVIEW_WRITER_SELECTORS, logger=None):
    if logger is None:
        logger = logging.getLogger()
    try:
        for sel_type, sel_value in REVIEW_WRITER_SELECTORS:
            if sel_type == "css":
                elems = await review.query_selector_all(sel_value)
            elif sel_type == "xpath":
                elems = await review.query_selector_all(f"xpath={sel_value}")
            else:
                continue
            for elem in elems:
                val = await elem.inner_text()
                if val:
                    logger.debug(f"[Playwright 추출][extract_writer_name] 추출 성공: {val}")
                    return str(val).strip()
        logger.debug("[Playwright 추출][extract_writer_name] 추출 결과 없음 (type: str)")
        return ""
    except Exception as e:
        logger.error(f"[Playwright 추출][extract_writer_name] 오류 발생 - {e}, selectors={REVIEW_WRITER_SELECTORS}")
        return ""

# async def extract_option(review, REVIEW_OPTION_SELECTORS, REVIEW_OPTION_EXCLUDE_KEYWORDS, logger=None):
#     if logger is None:
#         logger = logging.getLogger()
#     try:
#         option_texts = []
#         for selector in REVIEW_OPTION_SELECTORS:
#             elems = await review.query_selector_all(f"xpath={selector}")
#             for elem in elems:
#                 try:
#                     html = await elem.get_attribute("innerHTML")
#                     if html:
#                         # html = re.sub(r'<i[^>]*>\\|</i>', ' ', html)
#                         html = re.sub(r'<i[^>]*>.*?</i>', ' ', html)
#                         split_options = [t.strip() for t in html.split('|') if t.strip()]
#                         for text in split_options:
#                             if not any(ex_kw in text for ex_kw in REVIEW_OPTION_EXCLUDE_KEYWORDS):
#                                 option_texts.append(text)
#                 except Exception as e:
#                     logger.warning(f"[Playwright 추출][extract_option] 내부 옵션 추출 오류: {e}")
#                     text = await elem.inner_text()
#                     if text:
#                         text = text.strip()
#                         if not any(ex_kw in text for ex_kw in REVIEW_OPTION_EXCLUDE_KEYWORDS):
#                             option_texts.append(text)
#         option_texts = list(dict.fromkeys(option_texts))
#         option_texts = [" ".join(t.split()) for t in option_texts]
#         logger.debug(f"[Playwright 추출][extract_option] 추출 성공: {option_texts}")
#         return " ".join(option_texts)
#     except Exception as e:
#         logger.error(f"[Playwright 추출][extract_option] 오류 발생 - {e}, selectors={REVIEW_OPTION_SELECTORS}")
#         return ""

async def extract_option(review, REVIEW_OPTION_SELECTORS, REVIEW_OPTION_EXCLUDE_KEYWORDS, logger=None):
    if logger is None:
        logger = logging.getLogger()
    
    logger.debug(f"[Playwright 추출][extract_option] 실행, Selectors: {REVIEW_OPTION_SELECTORS}")
    try:
        all_option_texts = []
        
        # 설정 파일에 정의된 XPath selector들을 순회하며 옵션 컨테이너를 찾습니다.
        for selector in REVIEW_OPTION_SELECTORS:
            try:
                # query_selector_all을 사용하여 XPath와 일치하는 모든 요소를 가져옵니다.
                option_elements = await review.query_selector_all(f"xpath={selector}")

                for element in option_elements:
                    # JS 코드를 브라우저에서 실행하여 복잡한 DOM 구조를 처리합니다.
                    option_text = await element.evaluate('''
                        (element) => {
                            const texts = [];
                            // element의 직계 자식 노드들을 순회합니다.
                            for (const node of element.childNodes) {
                                // 노드 타입 3은 텍스트 노드를 의미합니다.
                                if (node.nodeType === Node.TEXT_NODE) { 
                                    const trimmedText = node.textContent.trim();
                                    if (trimmedText) {
                                        texts.push(trimmedText);
                                    }
                                }
                            }
                            // 추출된 텍스트들을 공백으로 연결합니다.
                            return texts.join(' ');
                        }
                    ''')

                    # 제외 키워드가 포함되지 않은 유효한 텍스트만 추가합니다.
                    if option_text and not any(ex_kw in option_text for ex_kw in REVIEW_OPTION_EXCLUDE_KEYWORDS):
                        all_option_texts.append(option_text)
            
            except Exception as e:
                logger.warning(f"[Playwright 추출][extract_option] 내부 옵션 추출 오류: {e}, selector={selector}")
                continue

        if not all_option_texts:
            logger.debug("[Playwright 추출][extract_option] 추출된 옵션 없음")
            return ""

        # 중복을 제거하고 최종 문자열로 합칩니다.
        final_options = " ".join(list(dict.fromkeys(all_option_texts)))
        clean_final_options = ' '.join(final_options.split()) # 최종 공백 정리
        
        logger.debug(f"[Playwright 추출][extract_option] 추출 성공: {clean_final_options}")
        return clean_final_options

    except Exception as e:
        logger.error(f"[Playwright 추출][extract_option] 오류 발생 - {e}")
        return ""

async def extract_is_verified(review, REVIEW_VERIFIED_SELECTORS, logger=None):
    if logger is None:
        logger = logging.getLogger()
    try:
        for selector in REVIEW_VERIFIED_SELECTORS:
            elems = await review.query_selector_all(f"xpath={selector}")
            if elems:
                logger.debug(f"[Playwright 추출][extract_is_verified] 추출 성공: True (type: bool)")
                return True
        logger.debug(f"[Playwright 추출][extract_is_verified] 추출 실패: False (type: bool)")
        return False
    except Exception as e:
        logger.error(f"[Playwright 추출][extract_is_verified] 오류 발생 - {e}, selectors={REVIEW_VERIFIED_SELECTORS}")
        return False

async def extract_first_text_by_selectors(review, selectors, logger=None):
    if logger is None:
        logger = logging.getLogger()
    try:
        for sel_type, sel_value in selectors:
            if sel_type == "css":
                elems = await review.query_selector_all(sel_value)
            elif sel_type == "xpath":
                elems = await review.query_selector_all(f"xpath={sel_value}")
            else:
                continue
            for elem in elems:
                val = await elem.inner_text()
                if val:
                    logger.debug(f"[Playwright 추출][extract_first_text_by_selectors] 추출 성공: {val}")
                    return str(val).strip()
        logger.debug(f"[Playwright 추출][extract_first_text_by_selectors] 추출 실패")
        return ""
    except Exception as e:
        logger.error(f"[Playwright 추출][extract_first_text_by_selectors] 오류 발생 - {e}, selectors={selectors}")
        return ""

async def extract_review_count(page, selectors, logger=None):
    if logger is None:
        logger = logging.getLogger()
    
    logger.debug(f"[Playwright 추출][extract_review_count] selectors: {selectors}")
    for sel_type, sel_value in selectors:
        try:
            if sel_type == "css":
                elems = await page.query_selector_all(sel_value)
            elif sel_type == "xpath":
                elems = await page.query_selector_all(f"xpath={sel_value}")
            else:
                continue

            for elem in elems:
                text = await elem.inner_text()
                if text:
                    text = text.strip()
                    # "No customer reviews" case
                    if "No customer reviews" in text:
                        logger.debug(f"[Playwright 추출][extract_review_count] 'No customer reviews' found.")
                        return 0
                    
                    # Regex for "N customer review(s)"
                    match = re.search(r"([0-9,]+)\s+customer review(s)?", text)
                    if match:
                        count_str = match.group(1).replace(",", "")
                        logger.debug(f"[Playwright 추출][extract_review_count] Extracted count: {count_str}")
                        return int(count_str)
        except Exception as e:
            logger.error(f"[Playwright 추출][extract_review_count] Error with selector {sel_type}:{sel_value} - {e}")
            continue

    logger.warning(f"[Playwright 추출][extract_review_count] Could not extract review count.")
    return 0

def parse_helpful(text, logger=None):
    if logger is None:
        logger = logging.getLogger()
    try:
        if not text:
            return 0
        text = str(text).strip()
        if "One person" in text:
            logger.debug(f"[Playwright 추출][parse_helpful] 1명 추출")
            return 1
        m = re.search(r"(\d+)", text.replace(",", ""))
        if m:
            logger.debug(f"[Playwright 추출][parse_helpful] 추출 성공: {m.group(1)}")
            return int(m.group(1))
        logger.debug(f"[Playwright 추출][parse_helpful] 추출 실패")
        return 0
    except Exception as e:
        logger.error(f"[Playwright 추출][parse_helpful] 오류 발생 - {e}, text={text}")
        return 0

def parse_rating(text, logger=None):
    if logger is None:
        logger = logging.getLogger()
    try:
        if not text:
            return 0.0
        m = re.search(r"([1-5](?:\.\d+)?)\\s*out of", text)
        if m:
            logger.debug(f"[Playwright 추출][parse_rating] 추출 성공: {m.group(1)}")
            return float(m.group(1))
        m = re.search(r"([1-5](?:\.\d+)?)", text)
        if m:
            logger.debug(f"[Playwright 추출][parse_rating] 추출 성공: {m.group(1)}")
            return float(m.group(1))
        logger.debug(f"[Playwright 추출][parse_rating] 추출 실패")
        return 0.0
    except Exception as e:
        logger.error(f"[Playwright 추출][parse_rating] 오류 발생 - {e}, text={text}")
        return 0.0

async def extract_review_star(review, REVIEW_STAR_SELECTORS, as_int=False, logger=None):
    if logger is None:
        logger = logging.getLogger()
    try:
        for sel_type, sel_value in REVIEW_STAR_SELECTORS:
            if sel_type == 'css':
                elems = await review.query_selector_all(sel_value)
            elif sel_type == 'xpath':
                elems = await review.query_selector_all(f"xpath={sel_value}")
            else:
                continue
            for elem in elems:
                rating_text = await elem.get_attribute('aria-label')
                if not rating_text:
                    try:
                        rating_text = await elem.inner_text()
                    except Exception:
                        rating_text = await elem.text_content()
                if rating_text:
                    star = parse_rating(rating_text, logger)
                    logger.debug(f"[Playwright 추출][extract_review_star] selector={sel_type}:{sel_value}, text={rating_text}, star={star}")
                    if star > 0:
                        return int(round(star)) if as_int else star
        logger.warning("[Playwright 추출][extract_review_star] 평점 추출 실패, 0 반환")
        return 0 if as_int else 0.0
    except Exception as e:
        logger.error(f"[Playwright 추출][extract_review_star] 오류 발생 - {e}, selectors={REVIEW_STAR_SELECTORS}")
        return 0 if as_int else 0.0

async def extract_next_page_btn(page, REVIEW_NEXT_PAGE_SELECTORS, logger=None):
    if logger is None:
        logger = logging.getLogger()
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
    return next_btn

async def extract_group_id(review, REVIEW_OPTION_SELECTORS, GROUP_ID_EXCLUDE_KEYWORDS, logger=None):
    if logger is None:
        logger = logging.getLogger()
    try:
        for selector in REVIEW_OPTION_SELECTORS:
            try:
                option_links = await review.query_selector_all(f"xpath={selector}")
                for link in option_links:
                    # 텍스트로 제외 키워드 필터링
                    text = await link.inner_text()
                    if text and any(ex_kw in text for ex_kw in GROUP_ID_EXCLUDE_KEYWORDS):
                        continue
                    href = await link.get_attribute('href')
                    if href:
                        match = re.search(r'/product-reviews/([A-Z0-9]{10})/', href)
                        if match:
                            group_id = match.group(1)
                            logger.debug(f"[extract_group_id] 옵션 href에서 group_id 추출 성공: {group_id}")
                            return group_id
            except Exception as e:
                logger.warning(f"[extract_group_id] selector 처리 중 오류: {e}, selector={selector}")
                continue
        logger.debug(f"[extract_group_id] 옵션 <a>에서 group_id 추출 실패")
        return None
    except Exception as e:
        logger.error(f"[extract_group_id] 전체 함수 오류: {e}")
        return None
