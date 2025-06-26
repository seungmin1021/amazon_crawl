# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


class AmazonCrawlerPipeline:
    def process_item(self, item, spider):
        return item


class CleanUnicodeCharsPipeline:
    def process_item(self, item, spider):
        for field in item:
            if isinstance(item[field], str):
                    item[field] = item[field].replace('\u200e', '').strip()
            
            if isinstance(item[field], dict):
                for x in item[field]:
                    if isinstance(item[field][x], str):
                        item[field][x] = item[field][x].replace('\u200e', '').strip()
        return item
