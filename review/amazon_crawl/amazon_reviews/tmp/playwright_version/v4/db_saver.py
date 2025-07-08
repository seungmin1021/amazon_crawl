import os
import json
from pymongo import MongoClient
from config import MONGO_HOST, MONGO_PORT, MONGO_DB, MONGO_COLLECTION, MONGO_USER, MONGO_PASSWORD

class MongoSaver:
    def __init__(self, host=None, port=None, db=None, collection=None, user=None, password=None):
        self.host = host or MONGO_HOST
        self.port = port or MONGO_PORT
        self.db_name = db or MONGO_DB
        self.collection_name = collection or MONGO_COLLECTION
        self.user = user or MONGO_USER
        self.password = password or MONGO_PASSWORD
        self.client = None
        self.db = None
        self.collection = None
        self._connect()

    def _connect(self):
        if self.user and self.password:
            mongo_uri = f"mongodb://{self.user}:{self.password}@{self.host}:{self.port}/"
        else:
            mongo_uri = f"mongodb://{self.host}:{self.port}/"
        self.client = MongoClient(mongo_uri)
        self.db = self.client[self.db_name]
        self.collection = self.db[self.collection_name]

    def save_json_file(self, json_path):
        if not os.path.exists(json_path):
            print(f"File not found: {json_path}")
            return 0
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            result = self.collection.insert_many(data)
            print(f"Inserted {len(result.inserted_ids)} documents from {os.path.basename(json_path)} into {self.db_name}.{self.collection_name}")
            return len(result.inserted_ids)
        else:
            result = self.collection.insert_one(data)
            print(f"Inserted 1 document from {os.path.basename(json_path)} into {self.db_name}.{self.collection_name}")
            return 1

    def save_latest_result(self, results_dir=None):
        results_dir = results_dir or os.path.join(os.getcwd(), "data", "results")
        files = [f for f in os.listdir(results_dir) if f.endswith(".json")]
        if not files:
            print("No result JSON files found.")
            return 0
        latest_file = max(files, key=lambda x: os.path.getctime(os.path.join(results_dir, x)))
        json_path = os.path.join(results_dir, latest_file)
        return self.save_json_file(json_path)

if __name__ == "__main__":
    saver = MongoSaver()
    saver.save_latest_result() 