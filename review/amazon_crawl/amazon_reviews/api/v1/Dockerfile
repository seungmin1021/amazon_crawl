# FastAPI + Uvicorn + PyMongo 기반 Amazon Reviews API Dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 환경변수로 MongoDB 접속정보 오버라이드 지원
ENV MONGO_HOST=localhost \
    MONGO_PORT=27017 \
    MONGO_DB=amazon_reviews \
    MONGO_COLLECTION=reviews

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
