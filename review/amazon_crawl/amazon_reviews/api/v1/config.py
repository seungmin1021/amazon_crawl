import os

MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
MONGO_PORT = os.getenv('MONGO_PORT', 27017)
MONGO_DB = os.getenv('MONGO_DB', 'amazon_reviews')
MONGO_COLLECTION = os.getenv('MONGO_COLLECTION', 'reviews')
MONGO_USER = os.getenv('MONGO_USER', '')
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', '')
