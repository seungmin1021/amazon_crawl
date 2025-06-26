# spiders/best_seller_spider.py
import random
import json
import time
from datetime import datetime
import asyncio

import scrapy
from scrapy.item import Item, Field
from scrapy.utils.project import get_project_settings
from scrapy_playwright.page import PageMethod


class AmazonProductItem(Item):
    crawl_date = Field()
    crawl_datetime = Field()
    product_name = Field()
    board_name = Field()
    price_before = Field()
    price_after = Field()
    ranking = Field()
    review_cnt = Field()
    asin = Field()
    error = Field()


class bestsellerSpider(scrapy.Spider):
    name = "best"
    allowed_domains = ["amazon.com"]

    # url ↔ board_name 매핑
    url_board_map = {
        "3015429011": "BEST_External SSD",
        "1292116011": "BEST_Internal SSD",
        "3151491": "BEST_Flash Drive",
        "3015433011": "BEST_Micro SD",
        "1197396": "BEST_SD",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        settings = get_project_settings()
        self.user_agents = settings.get("USER_AGENT_CHOICES")
        self.headers = settings.get("DEFAULT_REQUEST_HEADERS")
        self.m = {
            "playwright": True,
            "playwright_include_page": True,
            "playwright_page_methods": [
                PageMethod(
                    "evaluate",
                    """
                    async () => {
                        let scrollStep = 500;  
                        let delay = 500;       
                        let totalHeight = 0;

                        while (true) {
                            window.scrollBy(0, scrollStep);
                            await new Promise(resolve => setTimeout(resolve, delay));
                            let newHeight = document.body.scrollHeight;
                            totalHeight += scrollStep;

                            if (totalHeight >= newHeight) break;
                        }
                    }
                    """
                ),
                PageMethod("wait_for_timeout", 5000),
            ]
        }
        self.urls = [
            # external ssd / internal ssd / flash drive / micro sd / sd
            "https://www.amazon.com/Best-Sellers-Electronics-External-Solid-State-Drives/zgbs/electronics/3015429011",
            # "https://www.amazon.com/Best-Sellers-Computers-Accessories-Internal-Solid-State-Drives/zgbs/pc/1292116011",
            # "https://www.amazon.com/Best-Sellers-Computers-Accessories-USB-Flash-Drives/zgbs/pc/3151491",
            # "https://www.amazon.com/gp/bestsellers/pc/3015433011",
            # "https://www.amazon.com/Best-Sellers-Computers-Accessories-SecureDigital-Memory-Cards/zgbs/pc/1197396",
        ]

    # ───────────────────────────────────────── Requests
    def start_requests(self):
        with open("../amazon_crawler/config/amazon_cookies.json", "r") as f:
            cookies = json.load(f)
        c = {cookie['name']: cookie['value'] for cookie in cookies}
        self.logger.info("▶▶▶ start_requests() 호출")

        for url in self.urls:
            self.logger.info(f"크롤링 시작: {url}")
            ua = random.choice(self.user_agents)
            hdrs = self.headers.copy()
            hdrs["User-Agent"] = ua
            self.logger.debug(f"사용된 User-Agent: {ua}")
            yield scrapy.Request(
                url,
                callback=self.parse,
                errback=self.errback_handler,
                headers=hdrs,
                cookies=c,
                dont_filter=True,
                meta=self.m
            )

    # ───────────────────────────────────────── Parse
    def parse(self, response):
        """베스트셀러 50개 카드 파싱"""
        board_name = self._board_name_from_url(response.url)

        # 모든 가능한 셀렉터로 카드 찾기
        cards = response.xpath('//div[@id="gridItemRoot"]')
        self.logger.info(f"{board_name}: {len(cards)}개 카드 감지")

        # 30개만 나오는 경우 디버깅 정보 출력
        if len(cards) <= 30:
            self.logger.warning(f"⚠️  예상보다 적은 카드 수: {len(cards)}")
            

        for i, card in enumerate(cards, 1):
            item = AmazonProductItem()
            item["board_name"] = board_name
            item["crawl_datetime"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            item["crawl_date"] = datetime.now().strftime("%Y-%m-%d")

            # ─── 랭킹 (#1, #2 …)
            rank_selectors = [
                './/span[@class="zg-bdg-text"]/text()',
                './/span[contains(@class, "zg-bdg-text")]/text()',
                './/span[contains(@class, "zg-badge-text")]/text()'
            ]
            
            rank = None
            for selector in rank_selectors:
                rank = card.xpath(selector).get()
                if rank:
                    break
            item["ranking"] = rank.strip() if rank else f"#{i}"

            # ─── 제품명
            title_selectors = [
                './/div[contains(@class,"p13n-sc-css-line-clamp-3")]/text()',
                './/h3//text()',
                './/a[contains(@class, "a-link-normal")]//text()',
                './/span[contains(@class, "a-size-mini")]//text()',
                './/div[contains(@class, "a-section")]//text()'
            ]
            
            title = None
            for selector in title_selectors:
                title = card.xpath(selector).get()
                if title and title.strip():
                    break
            item["product_name"] = title.strip() if title else f"Product_{i}"

            # ─── 리뷰 수
            review_selectors = [
                './/a[contains(@href,"product-reviews")]/span/text()',
                './/span[contains(@class, "a-size-small")]//text()',
                './/a[contains(@href, "product-reviews")]//text()'
            ]
            
            reviews = None
            for selector in review_selectors:
                reviews = card.xpath(selector).get()
                if reviews and any(char.isdigit() for char in reviews):
                    break
            
            if reviews:
                # 숫자만 추출
                import re
                numbers = re.findall(r'[\d,]+', reviews)
                reviews = numbers[0] if numbers else "0"
            item["review_cnt"] = reviews.replace(",", "") if reviews else "0"

            # ─── 가격
            price_selectors = [
                './/span[contains(@class,"p13n-sc-price")]/text()',
                './/span[@class="a-price-whole"]/text()',
                './/span[contains(@class, "a-price")]//text()',
                './/span[contains(@class, "price")]//text()'
            ]
            
            price = None
            for selector in price_selectors:
                price = card.xpath(selector).get()
                if price and ('$' in price or any(char.isdigit() for char in price)):
                    break
            item["price_before"] = price.strip() if price else "null"
            item["price_after"] = price.strip() if price else "null"

            # ─── 상세 페이지 링크 (제품 URL)
            url_selectors = [
                './/a[contains(@class, "a-link-normal")]/@href',
                './/a[@role="link"]/@href',
                './/a/@href'
            ]

            product_url = None
            for selector in url_selectors:
                product_url = card.xpath(selector).get()
                if product_url and product_url.startswith('/'):
                    break

            # ─── ASIN 코드 추출
            asin = None
            if product_url:
                match = re.search(r"/dp/([A-Z0-9]{10})", product_url)
                if match:
                    asin = match.group(1)

            item["asin"] = asin if asin else "null"

            yield item
            
        next_page_url = response.xpath('//li[@class="a-last"]/a/@href').get()
        if next_page_url:
            next_page_url = response.urljoin(next_page_url)
            self.logger.info(f"다음 페이지 이동: {next_page_url}")

            ua = random.choice(self.user_agents)
            hdrs = self.headers.copy()
            hdrs["User-Agent"] = ua

            yield scrapy.Request(
                next_page_url,
                callback=self.parse,
                errback=self.errback_handler,
                headers=hdrs,
                cookies=response.request.cookies,
                dont_filter=True,
                meta=self.m
            )
        else:
            self.logger.info("더 이상 다음 페이지가 없습니다.")
            # 최종 결과 로그
        self.logger.info(f"🎯 {board_name} 크롤링 완료: 총 {len(cards)}개 상품 수집")

    # ───────────────────────────────────────── Errback
    def errback_handler(self, failure):
        request = failure.request
        item = AmazonProductItem()
        item["crawl_datetime"] = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        item["board_name"] = self._board_name_from_url(request.url)
        item["error"] = f"요청 실패: {failure.value}"
        self.logger.error(f"[Errback] {request.url} → {failure.value}")
        yield item

    # ───────────────────────────────────────── Helper
    def _board_name_from_url(self, url: str) -> str:
        """url 속 카테고리 코드로 board_name 추출"""
        for code, name in self.url_board_map.items():
            if code in url:
                return name
        return "unknown"


if __name__ == "__main__":
    from scrapy.crawler import CrawlerProcess
    from scrapy.utils.project import get_project_settings

    settings = get_project_settings()
    process = CrawlerProcess(settings)
    process.crawl(bestsellerSpider)
    process.start()