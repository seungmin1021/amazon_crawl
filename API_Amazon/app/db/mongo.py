from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client["mydb"]
collection = db["best_products"]
master_collection = db["product_master"]