# Amazon Reviews API (FastAPI)

아마존 리뷰 MongoDB 데이터를 REST API로 제공하는 FastAPI 기반 서버입니다.

## 📁 프로젝트 구조

```
api/v1/
├── config.py         # 중요 환경설정 (MongoDB 정보 등)
├── main.py           # FastAPI 앱 실행 진입점
├── router.py         # API 라우터 (실제 GET 엔드포인트 구현)
├── requirements.txt  # 의존성 패키지 목록
├── Dockerfile        # 도커 빌드 파일
├── README.md         # 프로젝트 설명서
└── __init__.py       # 패키지 인식용
```

## ⚙️ 환경설정

- MongoDB 연결 정보는 `config.py`에서 관리합니다.
- 기본값은 localhost:27017, DB명: `amazon_reviews`, 컬렉션: `reviews`입니다.

## 🚀 실행 방법

### 1. 로컬에서 직접 실행

```bash
# 의존성 설치
pip install -r requirements.txt

# 서버 실행
uvicorn main:app --reload
```

- 기본 포트: 8000
- API 문서: [http://localhost:8000/docs](http://localhost:8000/docs)

### 2. Docker로 실행

#### 1) 도커 이미지 빌드

```bash
docker build -t amazon-reviews-api .
```

#### 2) 도커 컨테이너 실행

```bash
docker run -d -p 8000:8000 --name amazon-reviews-api \
  -e MONGO_HOST=host.docker.internal \
  -e MONGO_PORT=27017 \
  -e MONGO_DB=amazon_reviews \
  -e MONGO_COLLECTION=reviews \
  amazon-reviews-api
```
- (로컬 MongoDB를 사용할 경우 `host.docker.internal` 사용)
- 환경변수로 MongoDB 접속정보를 오버라이드할 수 있습니다.

## 📝 API 사용법

### GET /reviews

#### 요청 파라미터
| 이름        | 타입   | 필수 | 설명                                  |
| ----------- | ------ | ---- | ------------------------------------- |
| last_seq    | int    | N    | 이 seq 이후 데이터만 조회             |
| req_dt      | str    | N    | 수집일자(YYYY-MM-DD) 이후 데이터만    |
| count       | int    | N    | 반환 데이터 수 (기본 100, 최대 500)   |
| access_key  | str    | N    | 인증키(현재 미사용, 빈 문자열 입력)   |

#### 예시 요청
```
GET http://localhost:8000/reviews?last_seq=100&req_dt=2025-06-01&count=100
```

#### 응답 예시
```
{
  "status": 200,
  "message": "OK",
  "remain_count": 100,
  "has_next": true,
  "total_count": 6498,
  "seq": 200,
  "result": [
    {
      "seq": 101,
      "crawl_date": "2025-06-01",
      ... (리뷰 데이터 필드 전체)
    },
    ...
  ]
}
```

- result 배열 내 각 리뷰의 필드는 MongoDB에 저장된 구조와 동일합니다.
- `_id` 필드는 반환하지 않습니다.

## 🛠️ 커스텀 환경변수
- 도커 실행 시 아래 환경변수로 MongoDB 접속정보를 오버라이드할 수 있습니다.
  - `MONGO_HOST`, `MONGO_PORT`, `MONGO_DB`, `MONGO_COLLECTION`

---

## 💬 문의/이슈
- 버그, 개선 요청 등은 개발자에게 직접 문의해 주세요.
