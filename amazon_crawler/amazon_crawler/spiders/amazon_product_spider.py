import scrapy 
from scrapy.item import Item, Field
from scrapy.utils.project import get_project_settings
from utils.helper_parse import (
    get_data_to_return,
    extract_product_title,
    check_page_validity,
    extract_style_info,
    set_board_name_and_division,
    determine_board_type,
    extract_image_url,
    set_data_gbn,
    combine_basic_expand_extract,
    extract_price_info,
    extract_rating_info
)

import pandas as pd
import random
import time
import json
from datetime import datetime   


class AmazonProductItem(Item):
    data_gbn = Field()
    last_crawl_datetime = Field()
    asin = Field()
    group_id = Field()
    board_name = Field()
    brand_name = Field()
    product_name = Field()
    division = Field()
    url = Field()
    flash_memory_size = Field()
    series = Field()
    style = Field()
    item_model_number = Field()
    hardware_platform = Field()
    item_weight = Field()
    product_dimensions = Field()
    color = Field()
    hard_drive_interface = Field()
    manufacturer = Field()
    country_of_origin = Field()
    date_first_available = Field()
    image_url = Field()

    expand_info = Field()
    error = Field()

class AmazonProductSpider(scrapy.Spider):
    name = 'amazon_product'
    allowed_domains = ['amazon.com']
    total_count = 0
    processed_count = 0

    def __init__(self, *args, **kwargs):
        super(AmazonProductSpider, self).__init__(*args, **kwargs)
        settings = get_project_settings()
        self.user_agents = settings.get('USER_AGENT_CHOICES')
        self.headers = settings.get('DEFAULT_REQUEST_HEADERS')

        # self.urls = ['https://www.amazon.com/dp/B007R9N0O0']

        # file_path = './data/amazon_review_open2.xlsx'
        # df = pd.read_excel(file_path, sheet_name='검증대상')


        file_path = './data/amazon_review_open.xlsx'
        df = pd.read_excel(file_path)

        df = df[df['DATA_GBN'] != 'DELETE']
        asin_list = df['ASIN'].dropna().unique().tolist()
        self.urls = [f'https://www.amazon.com/dp/{i}' for i in asin_list]
        # self.urls = random.sample(self.urls, 20)

        self.urls = sorted(self.urls)

        # self.urls = self.urls[:1000]
        # self.urls = self.urls[1000:2000]
        # self.urls = self.urls[2000:3000]
        # self.urls = self.urls[3000:4000]
        # self.urls = self.urls[4000:5000]
        self.urls = self.urls[5000:6000]
        # self.urls = self.urls[6000:7000]
        # self.urls = self.urls[7000:8000]
        # self.urls = self.urls[8000:]

        self.total_count = len(self.urls)

        with open("./config/selectors.json", "r", encoding="utf-8") as f:
            config = json.load(f)

        self.configs = config
        self.check_list = config['check_list']
        self.title_selectors = config["title_selectors"]
        self.row_selectors = config["row_selectors"]

    def start_requests(self):
        with open("./config/amazon_cookies.json", "r") as f:
            cookies = json.load(f)
        c = {cookie['name']: cookie['value'] for cookie in cookies}

        for url in self.urls:
            self.logger.info(f"크롤링 시작: {url}")
            ua = random.choice(self.user_agents)
            headers = self.headers.copy()
            headers['User-Agent'] = ua
            self.logger.debug(f"사용된 User-Agent: {ua}")
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                headers=headers,
                cookies=c,
                # cookies={
                #     "lc-main": "en_US",             
                #     "i18n-prefs": "USD",      
                #     "locale": "en_US",       
                # },
                dont_filter=True,
                errback=self.errback_handler,
            )

    def parse(self, response):
        """
        응답 파싱 및 제품 정보 추출
        """
        time.sleep(random.uniform(1, 2))
        url = response.meta.get('url', response.url)

        item = AmazonProductItem()
        for field in item.fields:
            item.setdefault(field, 'null')

        item['url'] = url
        item['last_crawl_datetime'] = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        item['asin'] = url.split('/')[-1]
        self.logger.info(f"[asin 디버그] : {item['asin']}")

        # 페이지 유효성 검사
        if check_page_validity(response, self.logger, item) is False:
            self.logger.warning(f"유효하지 않은 페이지: {url}")
            self.processed_count += 1
            return item
        
        try:
            item['expand_info'] = {}
            # 제품명 추출
            item['product_name'] = extract_product_title(response, self.title_selectors)
            # 제품 정보 추출
            combine_basic_expand_extract(response, self.logger, item, self.row_selectors, self.check_list)
            # 가격 정보 추출
            item['expand_info'].update(extract_price_info(response, self.logger, self.configs))
            # 별점, 리뷰수 추출
            extract_rating_info(response, self.configs, self.logger, item)
            # 스타일 정보 추출
            item['style'] = extract_style_info(response, self.logger)
            # 이미지 URL 추출
            item['image_url'] = extract_image_url(response, self.logger)
            # Best Seller 등급 설정
            set_data_gbn(item, self.logger)
            # 보드 타입 결정 및 설정
            board_type = determine_board_type(item, response)
            set_board_name_and_division(item, board_type)
            # data to return 객체 추출
            get_data_to_return(response, item, self.logger)

        except Exception as e:
            self.logger.error(f"데이터 추출 중 오류: {str(e)}")
            item['error'] = f"데이터 추출 중 오류: {str(e)}"

        self.processed_count += 1
        self.logger.info(f"진행도: {self.processed_count}/{self.total_count}")
        self.logger.info(f"제품 정보 추출 완료: {item['product_name'] if 'product_name' in item else url}")
        return item

    def errback_handler(self, failure):
        item = {}
        # 요청 정보 가져오기
        request = failure.request
        url = request.meta.get('url', request.url)
        
        title = failure.value.response.xpath('//title/text()').get('').lower()
        self.logger.info(f"요청 실패 title 검사 : {title}")
        if 'page not found' in title or '404' in title:
            item['url'] = url
            item['error'] = "Page not found or product not available"
            item['asin'] = url.split('/')[-1]
            item['data_gbn'] = 'DELETE'
            item['last_crawl_datetime'] = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
            self.logger.warning(f"errback: {url}")
            self.processed_count += 1
            return item
        
        # 오류 항목 생성
        item['url'] = url
        item['error'] = f"요청 실패: {failure.value}"
        item['asin'] = url.split('/')[-1]
        item['data_gbn'] = 'DELETE'
        item['last_crawl_datetime'] = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        self.processed_count += 1

        self.logger.error(f"요청 실패 ({url}): {failure.value}")
        return item

# 크롤러 실행 코드
if __name__ == '__main__':
    from scrapy.crawler import CrawlerProcess
    from scrapy.utils.project import get_project_settings
    
    process = CrawlerProcess(get_project_settings())
    process.crawl(AmazonProductSpider)
    process.start()