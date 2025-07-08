import requests
from bs4 import BeautifulSoup
import re
import time
import json

def extract_bestseller_items_v2(key):
    internal_ssd_url = 'https://www.amazon.com/Best-Sellers-Computers-Accessories-Internal-Solid-State-Drives/zgbs/pc/1292116011'
    external_ssd_url = 'https://www.amazon.com/Best-Sellers-Computers-Accessories-External-Solid-State-Drives/zgbs/pc/3015429011/ref=zg_bs_nav_pc_2_1292116011'

    if key == 'BEST_Internal SSD':
        url = internal_ssd_url
    elif key == 'BEST_External SSD':
        url = external_ssd_url
    else:
        return 'check key'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    items = []

    # 1. 베스트셀러 상품 박스 리스트 찾기
    product_boxes = soup.select('div.p13n-grid-content') 
    print(f"상품 박스 수: {len(product_boxes)}개 감지됨")
    
    # 2. 각 상품 박스 안에 있는 상품들 찾기
    product_items = soup.select('div.p13n-sc-uncoverable-faceout')
    print(f"상품 수: {len(product_items)}개 감지됨")
    
    for idx, block in enumerate(product_items, start=1):
        item_info = {'ranking': idx}
        item_info['board_name'] = key
        # 제품명
        try:
            title_elem = block.select_one("div._cDEzb_p13n-sc-css-line-clamp-3_g3dy1")
            if title_elem:
                item_info['title'] = title_elem.get_text(strip=True)
        except:
            item_info['title'] = None
        
        # 상품 링크
        try:
            link_elem = block.select_one("a.a-link-normal")
            if link_elem and link_elem.get('href'):
                item_info['link'] = "https://www.amazon.com" + link_elem['href']
        except:
            item_info['link'] = None
        
        # 가격
        try:
            price_elem = block.select_one("span._cDEzb_p13n-sc-price_3mJ9Z")
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price_match = re.search(r'([\d,.]+)', price_text)
                if price_match:
                    item_info['price_after'] = float(price_match.group(1).replace(',', ''))
        except:
            item_info['price_after'] = None
        
        # 별점
        try:
            rating_elem = block.select_one("i.a-icon-star-small span.a-icon-alt")
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                rating_match = re.search(r'([\d.]+)', rating_text)
                if rating_match:
                    item_info['rating'] = float(rating_match.group(1))
        except:
            item_info['rating'] = None
        
        # 리뷰 수
        try:
            review_elem = block.select_one("a.a-link-normal span.a-size-small")
            if review_elem:
                review_text = review_elem.get_text(strip=True)
                review_count = re.sub(r'[^\d]', '', review_text)
                if review_count.isdigit():
                    item_info['review_cnt'] = int(review_count)
        except:
            item_info['review_cnt'] = None
        
        items.append(item_info)

        time.sleep(0.2)  # 너무 빠른 요청 방지

    return items

#BEST_External SSD or BEST_Internal SSD
bestseller_items = extract_bestseller_items_v2('BEST_Internal SSD')

with open('./data/best_seller_info.json', 'w', encoding='utf-8') as f:
    json.dump(bestseller_items, f, indent=4, ensure_ascii=False)  


#제품 마스터 시퀀스, asin, data, datatime