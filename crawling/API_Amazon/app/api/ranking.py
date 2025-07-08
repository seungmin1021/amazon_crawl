from fastapi import APIRouter, Query
from app.core.config import settings
from app.db.mongo import collection

router = APIRouter()

@router.get("/ranking")
async def get_ranking(
    last_seq: int = Query(0),
    req_dt: str = Query(None),
    count: int = Query(10),
    access_key: str = Query(...)
):
    if access_key != settings.access_key:
        return {"status": 403, "message": "Invalid access key"}

    # MongoDB Aggregation Pipeline
    pipeline = []

    # 1. 필터 조건
    match_stage = {"$match": {}}
    if req_dt:
        match_stage["$match"]["crawl_date"] = req_dt
    if last_seq:
        match_stage["$match"]["seq"] = {"$gt": last_seq}
    pipeline.append(match_stage)

    # 2. master_collection 조인 (asin 기준)
    pipeline.append({
        "$lookup": {
            "from": "product_master",
            "localField": "asin",
            "foreignField": "asin",
            "as": "master_info"
        }
    })

    # 3. 리스트 형태로 들어온 master_info를 단일 문서로 (없어도 null 유지)
    pipeline.append({
        "$unwind": {
            "path": "$master_info",
            "preserveNullAndEmptyArrays": True
        }
    })

    # 4. 정렬 및 개수 제한
    pipeline.append({"$sort": {"seq": 1}})
    pipeline.append({"$limit": count})

    # 5. 실행 및 결과 조립
    cursor = collection.aggregate(pipeline)
    result = []

    async for doc in cursor:
        master = doc.get("master_info", {}) or {}
        expand_info = master.get("expand_info", {}) or {}

        result.append({
            "seq": doc.get("seq"),
            "crawl_date": doc.get("crawl_datetime", "").split(" ")[0] if doc.get("crawl_datetime") else None,
            "crawl_datetime": doc.get("crawl_datetime"),
            "asin": doc.get("asin"),
            "board_name": doc.get("board_name"),
            "price_before": expand_info.get("list_price"),
            "price_after": doc.get("price_after", 0),
            "ranking": doc.get("ranking"),
            "review_cnt": int(doc.get("review_cnt", 0)),
            "product_seq": master.get("seq"),
        })

    # 6. 전체 문서 수
    total_count = await collection.count_documents({})

    # 7. remain_count 계산
    if result:
        last_returned_seq = result[-1]["seq"]
        remain_count = await collection.count_documents({"seq": {"$gt": last_returned_seq}})
    else:
        remain_count = await collection.count_documents({"seq": {"$gt": last_seq}})

    has_next = remain_count > 0

    return {
        "status": 200,
        "message": "OK",
        "result": result,
        "remain_count": remain_count,
        "has_next": has_next,
        "total_count": total_count
    }
