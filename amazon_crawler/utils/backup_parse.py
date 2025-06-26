import re
import js2py
from parsel import Selector

def get_data_to_return(response, item, logger):
        items = {}
        script_tags = []

        script_tags.extend(response.xpath('//script[not(@src)]/text()').getall())
        script_tags.extend(response.xpath('//script/text()').getall())


        for node in response.xpath('//script[not(@src)]'):
            script_tags.append(node.xpath('string(.)').get())
                
        target_script = None
        for script in script_tags:
            if 'var dataToReturn' in script:
                target_script = script
                break

        if target_script:
            match = re.search(r'var\s+dataToReturn\s*=\s*({.*?});', target_script, re.DOTALL)
            if match:
                js_code = match.group(0)

                try:
                    context = js2py.EvalJs()
                    context.execute(js_code)

                    keys_to_extract = [
                        'currentAsin', 'landingAsin', 'parentAsin',
                        'dimensionToAsinMap', 'variationValues',
                        'num_total_variations', 'dimensionValuesDisplayData',
                        'variationDisplayLabels'
                    ]
                    
                    for key in keys_to_extract:
                        try:
                            value = getattr(context.dataToReturn, key)
                            if key == 'parentAsin':
                                item['group_id'] = value

                            if hasattr(value, 'to_dict'):
                                items[key] = value.to_dict()
                            elif hasattr(value, 'to_list'):
                                items[key] = value.to_list()
                            else:
                                items[key] = value
                        except Exception:
                            items[key] = None
                    item['expand_info'].update(items)
                    # self.logger.info(json.dumps(item, indent=4, ensure_ascii=False))
                except Exception as e:
                    logger.error(f"❌ JavaScript 실행 실패: {e}")
            else:
                item['dataToReturn'] = 'dataToReturn 객체를 찾을 수 없음'
                logger.warning("❌ dataToReturn 객체를 찾을 수 없음")
        else:
            item['dataToReturn'] = 'dataToReturn 스크립트를 찾을 수 없음'
            logger.warning("❌ dataToReturn 스크립트를 찾을 수 없음")


def check_page_validity(response, logger):
    """
    페이지가 유효한지 확인
    """
    # 페이지 타이틀 확인
    title = response.xpath('//title/text()').get('').lower()
    logger.info(f"페이지 유효 검사 추출 항목 : {title}")
    if 'page not found' in title or '404' in title:
        return False
    
    # 페이지 소스에서 "Page Not Found" 텍스트 확인
    if 'page not found' in response.body.decode('utf-8', errors='ignore').lower():
        return False
    
    if "api-services-support@amazon.com" in response.text or "captcha" in response.text.lower():
        logger.warning("로봇 페이지 감지됨")
        return False
    
    return True

def extract_product_title(response, title_selectors):
    # 여러 선택자를 시도하여 제목 찾기
    title = None
    for selector in title_selectors:
        if '::' in selector:  # CSS 선택자
            title_elements = response.css(selector).getall()
            if title_elements:
                title_raw = ' '.join([t.strip() for t in title_elements if t.strip()])
                if title_raw:
                    title = title_raw
                    break
        else:  # XPath 선택자
            title_elements = response.xpath(selector).getall()
            if title_elements:
                title_raw = ' '.join([t.strip() for t in title_elements if t.strip()])
                if title_raw:
                    title = title_raw
                    break
    
    # 더 넓은 범위로 검색 시도
    if not title:
        title_container = response.css('div#titleSection, div#title_feature_div, div#centerCol').extract_first()
        if title_container:
            # HTML에서 텍스트 추출 (임시)
            from scrapy.selector import Selector
            title_sel = Selector(text=title_container)
            texts = title_sel.css('h1 ::text, span.a-size-large ::text').getall()
            if texts:
                title = ' '.join([t.strip() for t in texts if t.strip()])

    if title:
        return title
    else:        
        return "제목을 찾을 수 없습니다."


def extract_basic_info(response, item, logger):
    items = {}
    try:
        rows = response.xpath('//table[contains(@class, "a-keyvalue") and contains(@class, "prodDetTable")]//tr')
        for row in rows:
            header = row.xpath('./th//text()').getall()
            value = row.xpath('./td//text()').getall()

            header = ''.join(header).strip() if header else None
            value = ''.join(value).strip() if value else None
            # print(f"[basic_info 디버그] header: {header}, value: {value}")

            if header and value and header != 'Customer Reviews':
                field_name = header.replace(' ', '_')
                items[field_name] = value

        if items == {}:
            detail_list = response.xpath('//div[@id="detailBullets_feature_div"]//ul/li')
            for li in detail_list:
                label = li.xpath('.//span[@class="a-text-bold"]/text()').get()
                value_parts = li.xpath('.//span[@class="a-list-item"]//text()[not(parent::span[contains(@class, "a-text-bold")])]').getall()
               
                label = re.sub(r'[_\s]{5,}', '', label) 
                label = label.strip().replace('\n', '').replace('\u200f', '').replace('\u200e', '').replace(":", "") if label else None
                value = ''.join(value_parts).strip() if value_parts else None

                if label and value:
                    if label != 'Customer Reviews':
                        field_name = label.replace(' ', '_')
                        items[field_name] = value

        item['basic_info'] = items

    except Exception as e:
        logger.error(f"상세 정보 추출 중 오류: {str(e)}")

def extract_expanded_details(response, item, row_selectors, logger):
    items = {}
    try:
        for selector in row_selectors:
            sel_value = selector['value'].strip()
            if not sel_value:
                continue

            rows = response.xpath(sel_value)
            print(f"[expand 디버그] selector: {sel_value}, rows 개수: {len(rows)}")

            if not rows:
                continue

            for row in rows:
                try:
                    header = row.xpath('normalize-space(./td[1])').get()
                    value = row.xpath('normalize-space(./td[2])').get()

                    print(f"[expand 디버그] header: {header}, value: {value}")

                    if header and value:
                        field_name = header.replace(' ', '_')
                        items[field_name] = value
                except Exception as inner_e:
                    logger.warning(f"row 처리 중 에러: {str(inner_e)}")

            if items:
                break

        if not items:
            print("[디버그] 확장 정보를 추출하지 못함")

        item['expand_details'] = items

    except Exception as e:
        logger.error(f"확장 정보 추출 중 오류: {str(e)}")


def extract_style_info(response, logger):
    """
    제품 스타일 정보 추출
    """
    try:
        style = response.css('#inline-twister-expanded-dimension-text-style_name::text').get()
        if style:
            return style.strip()
    except Exception as e:
        logger.error(f"스타일 정보 추출 중 오류: {str(e)}")
    return 'null'

def determine_board_type(item):
    """
    제품 정보를 기반으로 보드 타입 결정
    """
    # 설치 유형 확인
    installation_type = item.get('Installation_Type', '').lower()
    if 'external' in installation_type:
        return 'External SSD'
    elif 'internal' in installation_type:
        return 'Internal SSD'
    
    # 제품명으로 확인
    product_name = item.get('product_name', '').lower()
    if 'external' in product_name:
        return 'External SSD'
    elif 'internal' in product_name:
        return 'Internal SSD'
    elif 'micro' in product_name:
        return 'Micro SD'
    # 기본값 반환
    return 'Unknown'

def set_board_name_and_division(item, board_type):
    """
    보드 타입을 기반으로 board_name과 division 설정
    """
    # board_name 설정
    if item.get('data_gbn') == 'BEST':
        item['board_name'] = f'BEST_{board_type}'
    else:
        item['board_name'] = board_type
    
    # division 설정
    if board_type == 'External SSD':
        item['division'] = 'PSSD'
    elif board_type == 'Internal SSD':
        item['division'] = 'SSD'
    elif board_type == 'Micro SD':
        item['division'] = 'microSD'
    else:
        item['division'] = 'Unknown'

def extract_image_url(response, logger):
    """
    제품 이미지 URL 추출
    """
    try:
        # landingImage 이미지 속성 확인
        img_url = response.css('#landingImage::attr(data-old-hires)').get()
        if not img_url:
            img_url = response.css('#landingImage::attr(src)').get()
        return img_url if img_url else ''
    except Exception as e:
        logger.error(f"이미지 URL 추출 중 오류: {str(e)}")
        return ''

def set_data_gbn(item, logger):
    """
    베스트셀러 순위에 따라 데이터 구데이터분을 설정
    """
    try:
        best_sellers_text = item['expand_info']['Best_Sellers_Rank']

        if best_sellers_text:
            rank_num = int(best_sellers_text.split()[0][1:].replace(',',''))
            if rank_num <= 100:
                item['data_gbn'] = 'BEST'
            else:
                item['data_gbn'] = 'NORMAL'
        else:
            item['data_gbn'] = 'NORMAL'
    except Exception as e:
        logger.error(f"베스트셀러 순위 처리 중 오류: {str(e)}")
        item['data_gbn'] = 'NORMAL'

# 가격 정보 추출
def extract_price_match(sel: Selector, selectors: list[str], logger) -> str:
    for s in selectors:
        try:
            if '::' in s:
                value = sel.css(s).get()
            else:
                value = sel.xpath(s).get()
            if value:
                return value.strip()
        except Exception as e:
            continue
    return None

def extract_price_info(sel: Selector, logger, config: dict) -> dict:
    price = extract_price_match(sel, config.get("price_selectors", []), logger)
    if price:
        price = price.split(' ')[0]
    return {
        "price": price,
        "list_price": extract_price_match(sel, config.get("list_price_selectors", []), logger),
        "discount": extract_price_match(sel, config.get("discount_selectors", []), logger),
    }


# 별점, 리뷰수 추출 
def extract_rating_match(sel: Selector, selectors: list[str], logger) -> str:
    for s in selectors:
        try:
            value = sel.css(s).get() if '::' in s else sel.xpath(s).get()
            if value:
                return value.strip()
        except Exception as e:
            logger.error(f"별점(리뷰수) 처리 중 오류: {str(e)}")
            continue
    return None

def clean_rating(value: str) -> str:
    # 예: "4.6 out of 5 stars" → "4.6"
    if not value:
        return None
    match = re.search(r'(\d+(\.\d+)?)', value)
    return match.group(1) if match else None

def clean_review_count(value: str) -> str:
    # 예: "77,762 ratings" 또는 "(77,762)" → "77762"
    if not value:
        return None
    match = re.search(r'[\d,]+', value)
    return match.group().replace(',', '') if match else None

def extract_rating_info(sel: Selector, config: dict, logger, item) -> dict:
    raw_rating = extract_rating_match(sel, config.get("rating_selectors", []), logger)
    raw_reviews = extract_rating_match(sel, config.get("review_count_selectors", []), logger)
    item['rating'] = clean_rating(raw_rating)
    item['review_count'] = clean_review_count(raw_reviews)



# 기본 상세, 확장 정보 결합 추출
def combine_basic_expand_extract(response, logger, item, row_selectors):
    check_list = {
        'ASIN' : 'asin',
        'Brand' : 'brand_name',
        'Digital Storage Capacity' : 'flash_memory_size',
        'Hard Disk Size' : 'flash_memory_size',
        'Memory Storage Capacity' : 'flash_memory_size',
        'Series' : 'series',
        'Style' : 'style',
        'Model Number' : 'item_model_number',
        'Item model number' : 'item_model_number',
        'Compatible Devices' : 'hardware_platform',
        'Item Weight' : 'item_weight',
        'Item Dimensions L x W x Thickness' : 'product_dimensions',
        'Product Dimensions' : 'product_dimensions',
        'Item Dimensions LxWxH' : 'product_dimensions',
        'Color' : 'color',
        'Hard Disk Interface' : 'hard_drive_interface',
        'Hardware Interface' : 'hard_drive_interface',
        'Hard Drive Interface' : 'hard_drive_interface',
        'Manufacturer' : 'manufacturer',
        'Country of Origin' : 'country_of_origin',
        'Date First Available' : 'date_first_available'
    }
    key_list = list(check_list.keys())
    items = {}
    try:
        rows = response.xpath('//table[contains(@class, "a-keyvalue") and contains(@class, "prodDetTable")]//tr')
        for row in rows:
            header = row.xpath('./th//text()').getall()
            value = row.xpath('./td//text()').getall()

            header = ''.join(header).strip() if header else None
            value = ''.join(value).strip() if value else None
            # print(f"[basic_info 디버그] header: {header}, value: {value}")

            if header and value:
                if header in key_list:
                    item[check_list[header]] = value
                else:
                    if header != 'Customer Reviews':
                        field_name = header.replace(' ', '_')
                        items[field_name] = value

        detail_list = response.xpath('//div[@id="detailBullets_feature_div"]//ul/li')
        for li in detail_list:
            label = li.xpath('.//span[@class="a-text-bold"]/text()').get()
            value_parts = li.xpath('.//span[@class="a-list-item"]//text()[not(parent::span[contains(@class, "a-text-bold")])]').getall()
            
            label = re.sub(r'[_\s]{5,}', '', label) 
            label = label.strip().replace('\n', '').replace('\u200f', '').replace('\u200e', '').replace(":", "") if label else None
            value = ''.join(value_parts).strip() if value_parts else None

            if label and value:
                if label in key_list:
                    item[check_list[label]] = value
                else:
                    if label != 'Customer Reviews':
                        field_name = label.replace(' ', '_')
                        items[field_name] = value

        item['expand_info'] = items

        items2 = {}
        for selector in row_selectors:
            sel_value = selector['value'].strip()
            if not sel_value:
                continue

            rows = response.xpath(sel_value)
            # print(f"[expand 디버그] selector: {sel_value}, rows 개수: {len(rows)}")

            if not rows:
                continue

            for row in rows:
                try:
                    header = row.xpath('normalize-space(./td[1])').get()
                    value = row.xpath('normalize-space(./td[2])').get()

                    print(f"[expand 디버그] header: {header}, value: {value}")

                    if header and value:
                        if header in key_list:
                            item[check_list[header]] = value
                        else:
                            field_name = header.replace(' ', '_')
                            items2[field_name] = value
                except Exception as inner_e:
                    logger.warning(f"row 처리 중 에러: {str(inner_e)}")
            if items2:
                break
        item['expand_info'].update(items2)

    except Exception as e:
        logger.error(f"상세 정보 추출 중 오류: {str(e)}")