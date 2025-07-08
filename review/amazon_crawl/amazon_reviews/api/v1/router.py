from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from typing import Optional
from pymongo import MongoClient
from datetime import datetime
from config import MONGO_HOST, MONGO_PORT, MONGO_DB, MONGO_COLLECTION, MONGO_USER, MONGO_PASSWORD

router = APIRouter()

# MongoDB 인증정보를 반영하여 URI 생성
if MONGO_USER and MONGO_PASSWORD:
    mongo_uri = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/"
else:
    mongo_uri = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/"

client = MongoClient(mongo_uri)
db = client[MONGO_DB]
collection = db[MONGO_COLLECTION]

def parse_bool(val):
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.lower() in ("true", "1", "yes")
    return False

@router.get("/reviews")
def get_reviews(
    last_seq: Optional[int] = Query(None, description="last_seq 이후 데이터 조회"),
    req_dt: Optional[str] = Query(None, description="요청 일자(YYYY-MM-DD)"),
    count: int = Query(100, ge=1, le=500, description="반환 데이터 수 (기본 100, 최대 500)"),
    access_key: str = Query("", description="Access Key (현재 미사용)")
):
    query = {}
    if last_seq is not None:
        query["seq"] = {"$gt": last_seq}
    if req_dt:
        try:
            dt = datetime.strptime(req_dt, "%Y-%m-%d")
            query["crawl_date"] = {"$gte": dt.strftime("%Y-%m-%d")}
        except Exception:
            return JSONResponse(status_code=400, content={"status":400, "message":"Invalid req_dt format. Use YYYY-MM-DD."})

    # 전체 데이터 개수 (필터 없이 컬렉션 전체)
    total_count = collection.count_documents({})
    # 조건에 맞는 전체 개수 (remain_count 계산용)
    filtered_count = collection.count_documents(query)
    cursor = collection.find(query).sort("seq", 1).limit(count)
    results = list(cursor)

    remain_count = max(0, filtered_count - len(results))
    has_next = remain_count > 0

    for r in results:
        r.pop("_id", None)

    return {
        "status": 200,
        "message": "OK",
        "remain_count": remain_count,
        "has_next": has_next,
        "total_count": total_count,
        "result": results
    }
