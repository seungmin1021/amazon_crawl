from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

import js2py
import time
import json
import re
from datetime import datetime

def setup_driver():
    chrome_driver_path = './utils/chromedriver.exe' 

    options = Options()
    options.add_argument('--headless') 
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--start-maximized")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    service = Service(chrome_driver_path)
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def get_basic_product_info(product_info_section):
    product_info_rows = product_info_section.find_elements(By.XPATH, ".//tr")
    key_list = ['Hard Drive', 'Brand', 'Series', 'Hardware Platform', 'Item Weight', 
              'Product Dimensions', 'Color', 'Hard Drive Interface', 'Manufacturer', 
              'ASIN', 'Country of Origin', 'Date First Available', 'Hardware Interface', 'Item model number']
    product_info = {}
    best_sellers_rank_found = False
    best_sellers_rank = None
    
    for item in product_info_rows:
        try:
            header = item.find_element(By.XPATH, './/th').text.strip()
            value = item.find_element(By.XPATH, './/td').text.strip()
            if header in key_list:
                product_info[header] = value

            if header == 'Best Sellers Rank':
                best_sellers_rank_found = True
                best_sellers_rank = value
        except Exception as e:
            print(f"Error parsing row: {str(e)}")
    
    return product_info, best_sellers_rank_found, best_sellers_rank

def set_data_gbn(product_info, best_sellers_rank_found, best_sellers_rank):
    try:
        if best_sellers_rank_found:
            rank_num = int(best_sellers_rank.split()[0][1:].replace(',',''))
            if rank_num <= 100:
                product_info['data_gbn'] = 'BEST'
            else:
                product_info['data_gbn'] = 'NORMAL'
        else:
            product_info['data_gbn'] = 'NORMAL'
    except Exception as e:
        print(f"[ERROR] best_sellers_rank parsing 실패! 값: {best_sellers_rank}")
        print(f"[ERROR] 예외 메시지: {e}")
        product_info['data_gbn'] = 'NORMAL'
    
    return product_info

def get_product_title(driver):
    try:
        wait = WebDriverWait(driver, 10)
        title = wait.until(EC.presence_of_element_located((By.ID, 'productTitle'))).text.strip()
    except Exception as e:
        title = "제목을 찾을 수 없습니다."
        print(f"Error finding title: {e}")
    
    return title

def get_expanded_details(driver):
    expanded_details = {}
    try:
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        table = soup.find('table', {'class': 'a-normal a-spacing-micro'})

        if table:
            rows = table.find_all('tr')
            for row in rows:
                tds = row.find_all('td')
                
                if len(tds) >= 2:
                    key = tds[0].get_text(strip=True)
                    value = tds[1].get_text(strip=True)

                    if key and value:
                        expanded_details[key] = value
    except Exception as e:
        print(f"poExpander 추출 실패: {e}")
    
    return expanded_details

def get_style_info(driver):
    try:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        style_span = soup.find('span', id='inline-twister-expanded-dimension-text-style_name')

        if style_span:
            style_value = style_span.get_text(strip=True)
        else:
            style_value = ''  
        
        return style_value
    except Exception as e:
        print(f"style 추출 실패: {e}")
        return ''

def determine_board_type(product_info):
    board_type = None

    installation_type = product_info.get('Installation Type', '').lower()
    if 'external' in installation_type:
        board_type = 'External SSD'
    elif 'internal' in installation_type:
        board_type = 'Internal SSD'

    if not board_type:
        product_name_lower = product_info.get('product_name', '').lower()
        if 'external' in product_name_lower:
            board_type = 'External SSD'
        elif 'internal' in product_name_lower:
            board_type = 'Internal SSD'

    if not board_type:
        board_type = 'Micro SD'
    
    return board_type

def set_board_name_and_division(product_info, board_type):
    if product_info.get('data_gbn') == 'BEST':
        board_name = f'BEST_{board_type}'
    else:
        board_name = board_type
    
    product_info['board_name'] = board_name
    
    # division 설정
    if board_type == 'External SSD':
        product_info['division'] = 'PSSD'
    elif board_type == 'Internal SSD':
        product_info['division'] = 'SSD'
    elif board_type == 'Micro SD':
        product_info['division'] = 'microSD'
    else:
        product_info['division'] = 'Unknown'
    
    return product_info

def get_image_url(driver):
    try:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        img_tag = soup.find('img', id='landingImage')

        if img_tag and img_tag.has_attr('data-old-hires'):
            image_url = img_tag['data-old-hires']
        elif img_tag and img_tag.has_attr('src'):
            image_url = img_tag['src']
        else:
            image_url = ''
        
        return image_url
    except Exception as e:
        print(f"이미지 추출 실패: {e}")
        return ''

def product_detail_info(url):
    driver = setup_driver()

    driver.get(url)
    time.sleep(5)
    
    product_info = {}
    product_info['url'] = url
    
    try:
        product_info_section = driver.find_element(By.ID, "prodDetails")
        basic_info, best_sellers_rank_found, best_sellers_rank = get_basic_product_info(driver, product_info_section)
        product_info.update(basic_info)
        product_info = set_data_gbn(product_info, best_sellers_rank_found, best_sellers_rank)
        product_info['product_name'] = get_product_title(driver)
        expanded_details = get_expanded_details(driver)
        product_info.update(expanded_details)
        product_info['Style'] = get_style_info(driver)
        board_type = determine_board_type(product_info)
        product_info = set_board_name_and_division(product_info, board_type)
        product_info['image_url'] = get_image_url(driver)
        product_info['date'] = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        
    except Exception as e:
        print(f"제품 정보 추출 중 오류 발생: {e}")
    
    # print(json.dumps(product_info, indent=4, ensure_ascii=False))
    return product_info

def get_asin_list(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    asin_list = [i['ASIN'] for i in data]
    return asin_list

def save_to_json(data, filename="product_info_master.json"):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"데이터가 {filename}에 저장되었습니다.")


if __name__ == "__main__":
    asin_list = get_asin_list('./ASIN/asin.json')
    
    data = []
    for asin_code in asin_list:
        data.append(product_detail_info(f'https://www.amazon.com/dp/{asin_code}'))

    save_to_json(data)
    
    # product_detail_info('https://www.amazon.com/dp/B0BQX6NNVC')
