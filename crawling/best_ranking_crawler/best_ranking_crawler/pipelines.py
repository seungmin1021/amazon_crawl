# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import pymongo

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


class MongoPipeline:
    def __init__(self, mongo_uri, mongo_db, collection_name):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db
        self.collection_name = collection_name

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get("MONGO_URI", "mongodb://localhost:27017"),
            mongo_db=crawler.settings.get("MONGO_DATABASE", "amazon_reviews"),
            collection_name=crawler.settings.get("MONGO_COLLECTION", "product_master")
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]
        self.collection = self.db[self.collection_name]

    def close_spider(self, spider):
        self.client.close()

    def get_next_sequence(self, name):
        ret = self.db.counter.find_one_and_update(
            {"_id": name},
            {"$inc": {"seq": 1}},
            return_document=pymongo.ReturnDocument.AFTER
        )
        return ret["seq"]

    def process_item(self, item, spider):
        item_dict = dict(item)

        # seq 추가
        item_dict["seq"] = self.get_next_sequence("best_seq")

        # insert
        self.collection.insert_one(item_dict)

        spider.logger.info(f"MongoDB 저장 완료! (seq={item_dict['seq']})")
        return item
