from fastapi import APIRouter, Query
from app.core.config import settings
from app.db.mongo import master_collection 

router = APIRouter()

@router.get("/product")
async def get_product_list(
    last_seq: int = Query(0),
    count: int = Query(10),
    access_key: str = Query(...)
):
    if access_key != settings.access_key:
        return {"status": 403, "message": "Invalid access key"}

    # MongoDB 조건: seq > last_seq
    query = {"seq": {"$gt": last_seq}} if last_seq else {}

    # 정렬 + 제한
    cursor = master_collection.find(query).sort("seq", 1).limit(count)

    result = []
    async for doc in cursor:
        doc.pop("_id", None) 
        doc.pop("expand_info", None)
        result.append(doc)

    # 전체 문서 수
    total_count = await master_collection.count_documents({})

    # 남은 데이터 수
    if result:
        last_returned_seq = result[-1]["seq"]
        remain_count = await master_collection.count_documents({"seq": {"$gt": last_returned_seq}})
    else:
        remain_count = await master_collection.count_documents({"seq": {"$gt": last_seq}})

    has_next = remain_count > 0

    return {
        "status": 200,
        "message": "OK",
        "result": result,
        "remain_count": remain_count,
        "has_next": has_next,
        "total_count": total_count
    }
