import re
import js2py
from parsel import Selector

def check_page_validity(response, logger, item):
    """
    페이지가 유효한지 확인
    """
    # 페이지 타이틀 확인
    title = response.xpath('//title/text()').get('').lower()
    logger.info(f"페이지 유효 검사 추출 항목 : {title}")
    if 'page not found' in title:
        logger.warning("Page not found")
        item['error'] = "Page not found"
        return False
    
    # 페이지 소스에서 "Page Not Found" 텍스트 확인
    if 'page not found' in response.body.decode('utf-8', errors='ignore').lower():
        item['error'] = "Page not found"
        logger.warning("Page not found")
        return False
    
    if "api-services-support@amazon.com" in response.text or "captcha" in response.text.lower():
        item['error'] = "bot or captcha"
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

# 기본 상세, 확장 정보 결합 추출
def combine_basic_expand_extract(response, logger, item, row_selectors, c):
    check_list = c
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
            if label:
                label = re.sub(r'[_\s]{5,}', '', label) 
                label = label.strip().replace('\n', '').replace('\u200f', '').replace('\u200e', '').replace(":", "") if label else None
                value = ''.join(value_parts).strip() if value_parts else None
            # print(f"[li태그 디버그] header: {label}, value: {value}")
            if label and value:
                if label in key_list:
                    item[check_list[label]] = value
                else:
                    if label != 'Customer Reviews' or label.lower() != 'asin':
                        field_name = label.replace(' ', '_')
                        items[field_name] = value

        item['expand_info'] = items

        items2 = {}
        for selector in row_selectors:
            sel_value = selector['value'].strip()
            if not sel_value:
                continue

            rows = response.xpath(sel_value)
            if not rows:
                continue

            for row in rows:
                try:
                    header = row.xpath('normalize-space(./td[1])').get()

                    # truncate된 전체 텍스트 우선 추출
                    value = row.xpath('./td[2]//span[contains(@class, "a-truncate-full") and contains(@class, "a-offscreen")]/text()').get()

                    # 없으면 일반적인 텍스트 fallback (script 제외)
                    if not value:
                        value = row.xpath('./td[2]//text()[not(ancestor::script)]').getall()
                        value = ''.join(value).strip()

                    if header and value:
                        if header in key_list:
                            item[check_list[header]] = value
                        else:
                            field_name = header.replace(' ', '_')
                            items2[field_name] = value

                except Exception as inner_e:
                    logger.warning(f"row 처리 중 에러: {str(inner_e)}")

            if items2:
                item['expand_info'].update(items2)
                break
        # item['expand_info'].update(items2)

    except Exception as e:
        logger.error(f"상세 정보 추출 중 오류: {str(e)}")


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

def determine_board_type(item, resposne):
    """
    제품 정보를 기반으로 보드 타입 결정
    """
    product_name = item.get('product_name', '').lower()
    connectivity_technology = item.get('expand_info', {}).get('Connectivity_technology', '')
    hard_disk_description = item.get('expand_info', {}).get('Hard_Disk_Description', '')
    flash_memory_type = item.get('expand_info', {}).get('Flash_Memory_Type', '')
    hardware_connectivity = item.get('expand_info', {}).get('Hardware_Connectivity' '')
    hardware_interface = item.get('expand_info', {}).get('Hardware_Interface', '')
    installation_type = item.get('expand_info', {}).get('Installation_Type', '')
    
    external_keyword = ['external', 'exter','portable', 'usb', 'drive for mac', 'drive for pc', 'type-c']
    internal_keyword = ['internal', 'm.2', 'ide', 'sata', '2.5', 'pcie', '2280', 'gen4 x4', 'gen3 x4']
    sd_keyword = ['sdxc', 'sdhc', 'sd', 'secure digital card', 'tf card', 'tf memory card']
    ssd_keyword = ['ssd', 'solid state drive', 'solid state hard drive']

    category = extract_category(resposne, item)
    if category:
        if category == 'SD':
            if any(keyword in product_name for keyword in ['tf card', 'tf memory card', 'micro']):
                return 'Micro SD'
        return category
    
    # description -> name -> installation_type
    if hard_disk_description:
        hard_disk_description = hard_disk_description.lower()
        if any(keyword in hard_disk_description for keyword in ssd_keyword):
            if any(keyword in product_name for keyword in external_keyword):
                return 'External SSD'
            elif any(keyword in product_name for keyword in internal_keyword):
                return 'Internal SSD'
            else:
                if installation_type:
                    installation_type = installation_type.lower()
                    if 'external' in installation_type:
                        return 'External SSD'
                    elif 'internal' in installation_type:
                        return 'Internal SSD'
        else:
            if 'solid state drive' in product_name:
                if any(keyword in product_name for keyword in external_keyword):
                    return 'External SSD'
                elif any(keyword in product_name for keyword in internal_keyword):
                    return 'Internal SSD'
                else:
                    if installation_type:
                        installation_type = installation_type.lower()
                        if 'external' in installation_type:
                            return 'External SSD'
                        elif 'internal' in installation_type:
                            return 'Internal SSD'
    else:
        if any(keyword in product_name for keyword in ssd_keyword):
            if any(keyword in product_name for keyword in external_keyword):
                return 'External SSD'
            elif any(keyword in product_name for keyword in internal_keyword):
                return 'Internal SSD'
            else:
                if installation_type:
                    installation_type = installation_type.lower()
                    if 'external' in installation_type:
                        return 'External SSD'
                    elif 'internal' in installation_type:
                        return 'Internal SSD'


    if flash_memory_type:
        flash_memory_type = flash_memory_type.lower()
        if 'usb' in flash_memory_type:
            return 'Flash Drive'
        else:
            if connectivity_technology:
                connectivity_technology = connectivity_technology.lower()
                if 'usb' in connectivity_technology:
                    return 'Flash Drive'
                else:
                    if 'flash drive' in product_name:
                        return 'Flash Drive'
            else:
                if 'flash drive' in product_name:
                    return 'Flash Drive'
    else:    
        if connectivity_technology:
            if 'usb' in connectivity_technology:
                return 'Flash Drive'
            else:
                if 'flash drive' in product_name:
                    return 'Flash Drive'
        else:
            if 'flash drive' in product_name:
                return 'Flash Drive'
        

    if flash_memory_type:
        flash_memory_type = flash_memory_type.lower()
        if any(keyword in flash_memory_type for keyword in sd_keyword):
            if 'micro' in flash_memory_type or 'tf card' in flash_memory_type:
                return 'Micro SD'
            else:
                if 'micro' in product_name:
                    return 'Micro SD'
                return 'SD'
    elif hardware_connectivity:
        hardware_connectivity = hardware_connectivity.lower()
        if any(keyword in hardware_connectivity for keyword in sd_keyword):
            if 'micro' in hardware_connectivity or 'tf card' in hardware_connectivity:
                return 'Micro SD'
            else:
                if 'micro' in product_name:
                    return 'Micro SD'
                return 'SD'
    elif hardware_interface:
        hardware_interface = hardware_interface.lower()
        if any(keyword in hardware_interface for keyword in sd_keyword):
            if 'micro' in hardware_interface or 'tf card' in hardware_interface:
                return 'Micro SD'
            else:
                if 'micro' in product_name:
                    return 'Micro SD'
                return 'SD'
    else:
        if any(keyword in product_name for keyword in sd_keyword):
            if 'micro' in product_name or 'tf card' in product_name:
                return 'Micro SD'
            else:
                return 'SD'
    return 'Unknown'

def set_board_name_and_division(item, board_type):
    """
    보드 타입을 기반으로 board_name과 division 설정
    """
    # board_name 설정
    if board_type != 'Unknown':
        if item.get('data_gbn') == 'BEST':
            item['board_name'] = f'BEST_{board_type}'
        else:
            item['board_name'] = board_type
    else:
        item['board_name'] = 'Unknown'
    
    # division 설정
    if board_type == 'External SSD':
        item['division'] = 'PSSD'
    elif board_type == 'Internal SSD':
        item['division'] = 'SSD'
    elif board_type == 'Micro SD':
        item['division'] = 'microSD'
    elif board_type == 'SD':
        item['division'] = 'SD'
    elif board_type == 'Flash Drive':
        item['division'] = 'Flash Drive'
    else:
        item['division'] = 'Unknown'


# dataToReturn 객체 추출
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
                                if value != None:
                                    item['group_id'] = value
                                else:
                                    item['group_id'] = item['asin']

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
                logger.warning("❌ dataToReturn 객체를 찾을 수 없음")
        else:
            logger.warning("❌ dataToReturn 스크립트를 찾을 수 없음")


# 가격 정보 추출
def extract_price_match(sel: Selector, selectors: list[str]) -> str:
    for s in selectors:
        try:
            if '::' in s:
                value = sel.css(s).get()
            else:
                value = sel.xpath(s).get()
            if value:
                return value.strip()
        except Exception as e:
            print(f'가격 정보 추출 중 에러 : {e}')
            continue
    return None

def extract_price_info(sel: Selector, logger, config: dict) -> dict:
    price = extract_price_match(sel, config.get("price_selectors", []))
    if price:
        price = price.split(' ')[0]
    return {
        "price": price,
        "list_price": extract_price_match(sel, config.get("list_price_selectors", [])),
        "discount": extract_price_match(sel, config.get("discount_selectors", [])),
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
    if not value:
        return None
    match = re.search(r'(\d+(\.\d+)?)', value)
    return match.group(1) if match else None

def clean_review_count(value: str) -> str:
    if not value:
        return None
    match = re.search(r'[\d,]+', value)
    return match.group().replace(',', '') if match else None

def extract_rating_info(sel: Selector, config: dict, logger, item) -> dict:
    raw_rating = extract_rating_match(sel, config.get("rating_selectors", []), logger)
    raw_reviews = extract_rating_match(sel, config.get("review_count_selectors", []), logger)
    item['expand_info'].update({'rating': clean_rating(raw_rating),
                                'review_count': clean_review_count(raw_reviews)})
    

def extract_category(response, item):
    category = response.xpath(
        '//div[@id="wayfinding-breadcrumbs_feature_div"]//ul/li[last()]/span/a/text()'
    ).get()

    # category = response.css(
    #     '#wayfinding-breadcrumbs_feature_div ul li span a::text'
    # ).getall()[-1]

    if category == "Micro SD Cards":
        return "Micro SD"
    elif category == "SD Cards":
        return "SD"
    elif category == "Internal Solid State Drives":
        return "Internal SSD"
    elif category == "External Solid State Drives":
        return "External SSD"
    elif category == "USB Flash Drives":
        return "Flash Drive"
    else:
        return False
    