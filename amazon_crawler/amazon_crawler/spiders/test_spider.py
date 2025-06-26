from scrapy import Spider, Request
from scrapy_playwright.page import PageMethod

class EventsSpider(Spider):
    """Handle page events and extract the first clickable link."""
    
    name = 'clickable'

    def start_requests(self):
        yield Request(
            url='https://apify.com/store',
            meta={
                "playwright": True,
                # Include the page object in the response
                "playwright_include_page": True,
                "playwright_page_methods": [
                     # Wait for the search input to be loaded
                    PageMethod("wait_for_selector", 'input[data-test="actor-store-search"]'),
                    PageMethod("fill", 'input[data-test="actor-store-search"]', 'tiktok'),
                    PageMethod("click", 'input[data-test="actor-store-search"] + svg'),
                    # Wait 1 second for the next page to load
                    PageMethod("wait_for_timeout", 1000),
                ],
            },
            callback=self.parse
        )

    async def parse(self, response, **kwargs):
        # Use the Playwright page object included in the response
        page = response.meta['playwright_page']
        previous_height = await page.evaluate("document.body.scrollHeight")
        while True:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)  # Wait for 2 seconds for new content to load
            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height == previous_height:
                break
            previous_height = new_height
        # Find all Actor Cards on the page
        actor_cards = await page.query_selector_all('a[data-test="actor-card"]')
        actor_data = []

        # Get data from to the first five Actors
        for actor_card in actor_cards[:5]:
            url = await actor_card.get_attribute('href')
            actor_name_element = await actor_card.query_selector('div.ActorStoreItem-title h3')
            actor_name = await actor_name_element.inner_text()
            actor_data.append(
                {
                    "url": url,
                    "actor_name": actor_name
                }
            )

        yield {'actors_data': actor_data}
        
        # Close the page
        await page.close()