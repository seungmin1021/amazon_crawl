# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


class AmazonCrawlerSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    async def process_start(self, start):
        # Called with an async iterator over the spider start() method or the
        # maching method of an earlier spider middleware.
        async for item_or_request in start:
            yield item_or_request

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class AmazonCrawlerDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)

import random
import time
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.utils.response import response_status_message
import logging
from threading import Timer

class CustomRetryMiddleware(RetryMiddleware):
    """차단 감지 및 재시도 관리 미들웨어"""
    
    def process_response(self, request, response, spider):
        if request.meta.get('dont_retry', False):
            return response
        
        if response.status in self.retry_http_codes:
            reason = response_status_message(response.status)
            # 차단 감지 시 더 긴 대기 시간
            if response.status in [403, 429]:
                spider.logger.warning(f"차단 감지됨: {response.url}, 더 긴 대기 시간 적용")
                time.sleep(random.uniform(30, 60))
            return self._retry(request, reason, spider) or response

        return response

class RandomUserAgentMiddleware:
    """무작위 User-Agent 미들웨어"""
    
    def process_request(self, request, spider):
        user_agent = random.choice(spider.settings.getlist('USER_AGENT_CHOICES'))
        request.headers['User-Agent'] = user_agent
        return None


class CustomProxyMiddleware:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.proxies = []
        self.current_index = 0
        self.errors = {}
        self.unhealthy = set()
        self.recovery_time = 30 * 60  # 30분

    def process_request(self, request, spider):
        if not self.proxies or request.meta.get('dont_proxy'):
            return

        proxy = self._get_proxy()
        if proxy:
            request.meta['proxy'] = proxy
            self.logger.debug(f"[Proxy] Using: {proxy}")

    def process_response(self, request, response, spider):
        proxy = request.meta.get('proxy')
        if proxy and response.status in {403, 429, 502, 503, 504}:
            self._mark_error(proxy)
            self.logger.warning(f"[Proxy Error] {proxy} | Status: {response.status}")
        return response

    def process_exception(self, request, exception, spider):
        proxy = request.meta.get('proxy')
        if proxy:
            self._mark_error(proxy)
            self.logger.error(f"[Proxy Exception] {proxy} | {exception}")
        return None

    def _get_proxy(self):
        healthy = [p for p in self.proxies if p not in self.unhealthy]
        if not healthy:
            return random.choice(self.proxies)

        self.current_index = (self.current_index + 1) % len(healthy)
        return healthy[self.current_index]

    def _mark_error(self, proxy):
        self.errors[proxy] = self.errors.get(proxy, 0) + 1
        if self.errors[proxy] >= 3:
            self.unhealthy.add(proxy)
            self.logger.warning(f"[Unhealthy] {proxy} → Retry in {self.recovery_time // 60} min")
            Timer(self.recovery_time, self._recover_proxy, args=[proxy]).start()

    def _recover_proxy(self, proxy):
        self.unhealthy.discard(proxy)
        self.errors[proxy] = 0
        self.logger.info(f"[Recovered] {proxy} is back")

    @classmethod
    def from_crawler(cls, crawler):
        mw = cls()
        mw.proxies = crawler.settings.getlist('PROXIES', [])
        mw.recovery_time = crawler.settings.getint('PROXY_RECOVERY_TIME', 1800)
        if mw.proxies:
            mw.logger.info(f"[Loaded] {len(mw.proxies)} proxies from settings")
        return mw
