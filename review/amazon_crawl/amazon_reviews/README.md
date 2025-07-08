# Amazon Reviews Data Pipeline

이 프로젝트는 아마존 제품 리뷰 데이터를 **크롤링 → DB 적재 → REST API 제공**까지 end-to-end로 처리하는 시스템입니다.

- `amazon_reviews/crawler/` : 리뷰 크롤러 및 MongoDB 적재 (Python, Selenium, Playwright)
- `amazon_reviews/api/`     : MongoDB에 저장된 리뷰 데이터를 REST API로 제공 (Python, FastAPI)

---

# Amazon Product Review Crawler (Playwright + Selenium)

## 프로젝트 개요

이 프로젝트는 아마존(amazon.com) 제품의 리뷰 데이터를 **대량/자동/병렬**로 수집하는 크롤러입니다.  
- Selenium을 활용한 로그인 세션 확보  
- Playwright 기반의 비동기 병렬 크롤링  
- 엑셀로 ASIN 목록 관리  
- robust한 예외처리, 상세 로깅, 프록시/VPN, CAPTCHA 대응  
- 크롤링 결과를 MongoDB에 저장, REST API로 조회 가능

---

## 디렉토리/파일 구조

```
amazon_reviews/
  ├── crawler/
  │   └── v1/
  │       ├── main.py                # 실행 진입점 (전체 파이프라인 제어)
  │       ├── config.py              # 환경설정, 계정/프록시/경로/셀렉터 등
  │       ├── browser.py             # Selenium/Selenium-wire 브라우저/프록시 세팅
  │       ├── login.py               # 아마존 로그인, CAPTCHA/2차 인증 robust 대응
  │       ├── crawler.py             # Playwright 기반 리뷰 크롤링(비동기/병렬)
  │       ├── extractors_playwright.py # Playwright용 리뷰 정보 추출 함수
  │       ├── db_saver.py            # MongoDB 적재 유틸리티
  │       ├── utils.py               # 엑셀 로드, 결과 저장 등 유틸리티
  │       ├── timer.py               # 크롤링 성능/요약 저장
  │       ├── logger.py              # 로그 관리
  │       ├── requirements.txt       # Python 패키지 목록
  │       ├── Dockerfile             # Docker 빌드 파일
  │       ├── README.md           # (본 문서)
  │       ├── data/
  │       │   ├── ASIN/              # 입력 엑셀/CSV/JSON (크롤링 대상 ASIN)
  │       │   ├── results/           # 크롤링 결과 JSON
  │       │   ├── failed/            # 실패 ASIN JSON
  │       │   └── pdf/               # (옵션) PDF 저장
  │       ├── logs/                  # 실행 로그
  │       ├── html/                  # 디버깅용 HTML
  │       └── tmp/                   # (구버전/임시 백업)
  └── api/
      └── v1/                        # (REST API 서버, 별도 운영)
```

---

## API 서버 (amazon_reviews/api/v1)

- FastAPI 기반 REST API 서버
- MongoDB에 저장된 리뷰 데이터를 `/reviews` 엔드포인트로 조회 가능
- 주요 파일: main.py, router.py, config.py, requirements.txt, Dockerfile

### 실행 예시
```bash
cd amazon_reviews/api/v1
pip install -r requirements.txt
uvicorn main:app --reload
# 또는 Docker로 실행
docker build -t amazon-reviews-api .
docker run -d -p 8000:8000 --name amazon-reviews-api \
  -e MONGO_HOST=host.docker.internal \
  -e MONGO_PORT=27017 \
  -e MONGO_DB=amazon_reviews \
  -e MONGO_COLLECTION=reviews \
  amazon-reviews-api
```

### 주요 엔드포인트

- `GET /reviews`  
  - 파라미터: last_seq, req_dt, count 등
  - MongoDB에서 조건에 맞는 리뷰 데이터 반환
  - 예시:  
    ```
    GET http://localhost:8000/reviews?last_seq=100&req_dt=2025-06-01&count=100
    ```
  - 응답:  
    ```json
    {
      "status": 200,
      "message": "OK",
      "remain_count": 100,
      "has_next": true,
      "total_count": 6498,
      "result": [ ... ]
    }
    ```

---

## 전체 파이프라인 요약

1. **크롤러 실행**  
   → 엑셀/CSV에서 ASIN 목록 로드  
   → Selenium+Playwright로 리뷰 크롤링  
   → 결과를 MongoDB에 적재

2. **API 서버 실행**  
   → FastAPI로 MongoDB 데이터 REST API 제공  
   → 외부 시스템/프론트엔드/분석툴 등에서 REST API로 데이터 활용

---

## 가상환경 및 설치

### 1. Python 가상환경 생성 (권장)
```bash
python -m venv venv
source venv/bin/activate  # (Windows: venv\\Scripts\\activate)
```

### 2. 필수 패키지 설치
```bash
pip install --upgrade pip
pip install -r requirements.txt
```
- 주요 패키지: playwright, selenium, selenium-wire, pandas, openpyxl, numpy, requests, pymongo, python-dotenv 등

### 3. Playwright 브라우저 바이너리 설치
```bash
playwright install
```

---

## 환경 변수(.env) 설정

`.env` 파일 예시:
```
AMAZON_ACCOUNTS=이메일1::비번1,이메일2::비번2
PROXIES=45.150.81.133:12323@id:pw,1.2.3.4:5678@id2:pw2
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_DB=amazon_reviews
MONGO_COLLECTION=reviews
MONGO_USER=admin
MONGO_PASSWORD=adminpw
```
- **AMAZON_ACCOUNTS**: 여러 계정 지원, 콤마로 구분, 각 쌍은 `이메일::비번`
- **PROXIES**: 여러 프록시 지원, 콤마로 구분, 각 프록시는 `호스트:포트@아이디:비번` 형식
- **MongoDB 정보**: DB 접속 정보, 보안을 위해 반드시 .env에만 저장

---

## 실행 방법 및 주요 인자

### 1. 기본 실행 예시
```bash
python main.py --login_browser firefox --login_headless --crawling_headless --use_proxy --asin_start 0 --asin_end 10 --max_pages 3 --max_concurrent_contexts 5 --log_level DEBUG
```

### 2. 주요 인자 설명
- `--login_browser`: 로그인 브라우저 (firefox/chrome)
- `--login_headless`: 로그인 단계 headless 모드
- `--crawling_headless`: 리뷰 크롤링 단계 headless 모드
- `--use_proxy`: 프록시 사용 여부
- `--asin_start`, `--asin_end`: 엑셀에서 ASIN 슬라이싱 범위
- `--max_pages`: 각 상품별 최대 크롤링 페이지 수
- `--max_concurrent_contexts`: Playwright 동시 context 개수(병렬성)
- `--log_level`: 로그 레벨 (DEBUG/INFO 등)

### 3. 다양한 실행 예시
- 크롬, 프록시 미사용, 100개 ASIN, 5페이지씩:
  ```bash
  python main.py --login_browser chrome --asin_start 0 --asin_end 100 --max_pages 5 --max_concurrent_contexts 3 --log_level INFO
  ```
- headless 해제(실제 브라우저 창 확인), 10개만 테스트:
  ```bash
  python main.py --login_browser firefox --asin_start 0 --asin_end 10 --max_pages 2
  ```
- 프록시 사용, 로그 레벨 WARNING:
  ```bash
  python main.py --use_proxy --log_level WARNING
  ```

---

### 4, CAPTCHA 수동 해결 방식

아마존에서 CAPTCHA(자동화 방지) 페이지가 반복적으로 뜨는 경우, 아래와 같이 VNC를 활용해 수동으로 해결할 수 있습니다.

```bash
# Xvfb 설치
sudo apt update
sudo apt install xvfb x11vnc
```

```bash
# 1. 모든 프로세스 종료 및 lock 파일 삭제
killall Xvfb
killall x11vnc
killall firefox
rm -f /tmp/.X99-lock
# 2. Xvfb 실행 3. DISPLAY 환경변수 설정
Xvfb :99 -screen 0 1920x1080x24 & export DISPLAY=:99
# 4. x11vnc 실행
x11vnc -display :99 -nopw -listen localhost -xkb

# 5. VNC 뷰어 실행 (다른 터미널에서)
vncviewer localhost:5900
# 6. 크롤러 실행 (다른 터미널에서, export DISPLAY=:99 한 후)
python main.py --login_browser firefox --login_headless --crawling_headless --use_proxy --asin_start 0 --asin_end 10 --max_pages 3 --max_concurrent_contexts 5 --log_level DEBUG
```

> **설명:**
> - Xvfb로 가상 디스플레이를 띄우고, x11vnc로 원격 접속 가능하게 만든 뒤, VNC 뷰어로 직접 브라우저를 조작해 CAPTCHA를 수동으로 풀 수 있습니다.
---

## Docker 환경 구축

### 1. 빌드 및 실행
```bash
docker build -t amazon-crawler:v1 .
docker run --rm -v $PWD/data:/app/data -v $PWD/logs:/app/logs -v $PWD/.env:/app/.env amazon-crawler:v1
```
- Dockerfile, requirements.txt, main.py 등 모든 소스가 v1 폴더에 있어야 함

### 2. Docker Compose 예시
`docker-compose.yml` 예시(별도 작성 필요):
```yaml
version: '3.8'
services:
  mongo:
    image: mongo:latest
    ports:
      - "27017:27017"
    volumes:
      - ./mongo_data:/data/db
  crawler:
    build: .
    depends_on:
      - mongo
    environment:
      MONGO_HOST: mongo
      MONGO_PORT: 27017
      MONGO_DB: amazon_reviews
      MONGO_COLLECTION: reviews
      MONGO_USER: admin
      MONGO_PASSWORD: adminpw
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./.env:/app/.env
    command: --login_browser firefox --login_headless --crawling_headless --use_proxy --asin_start 0 --asin_end 30 --max_pages 3 --max_concurrent_contexts 5 --log_level DEBUG
```

---

## 데이터 흐름 및 저장 구조

### 1. 입력 데이터
- `data/ASIN/amazon_review_open_YYYYMMDD.xlsx` : 크롤링 대상 ASIN 및 메타데이터 엑셀/CSV/JSON

### 2. 크롤링 결과물
- `data/results/ASIN_REVIEWS_Excel_YYYYMMDDHHMMSS_DEBUG.json` : ASIN별 메타데이터 포함 전체 결과
- `data/results/ASIN_REVIEWS_Excel_YYYYMMDDHHMMSS.json` : DB 적재용 평탄화 리뷰 리스트
- `data/failed/failed_ASIN_list_YYYYMMDDHHMMSS.json` : 실패한 ASIN 및 사유
- `data/results/ASIN_REVIEWS_Excel_YYYYMMDDHHMMSS_timer.json` : 크롤링 요약/성능
- `logs/amazon_crawler_YYYYMMDD_HHMMSS.log` : 상세 로그
- `html/` : 디버깅용 HTML

### 3. MongoDB 적재
- 크롤링 결과는 `db_saver.py`를 통해 MongoDB에 저장
- 환경변수(.env)에서 DB 접속 정보 자동 로드
- 각 리뷰에 고유 seq 부여, 컬렉션명은 `MONGO_COLLECTION` 사용

---

## 유지보수/확장 포인트

- **프록시/계정/DB 정보는 반드시 .env로 관리** (보안)
- **코드 구조가 명확하게 분리** (로그인, 크롤링, DB, 유틸리티 등)
- **입출력 포맷, DB 스키마, 주요 함수/클래스 주석** 꼼꼼히 확인
- **tmp/ 디렉토리는 구버전/임시 백업용, 무시 가능**
- **API 서버(amazon_reviews/api/v1)는 별도 운영, REST API로 데이터 조회 가능**

---

## 예시: 크롤링 결과 JSON 구조

### [1] ASIN별 전체 결과 (DEBUG)
```json
[
  {
    "ASIN": "B08YCYS58M",
    "result": [
      {
        "seq": 0,
        "title": "Great product!",
        "content": "...",
        "star": 5,
        "writer_nm": "John Doe",
        "write_dt": "2024-06-24",
        ...
      }
    ],
    "crawl_review_cnt": 1
  }
]
```

### [2] DB 적재용 평탄화 리뷰 리스트
```json
[
  {
    "seq": 0,
    "ASIN": "B08YCYS58M",
    "title": "Great product!",
    "content": "...",
    "star": 5,
    "writer_nm": "John Doe",
    "write_dt": "2024-06-24",
    ...
  }
]
```

---

## 문의/기여/유지보수

- 코드/구조/실행/확장 관련 문의는 README 상단 또는 소스 내 주석 참고
- 유지보수자는 반드시 .env, requirements.txt, Dockerfile, config.py, main.py, db_saver.py 등 최신화 여부 확인
- tmp/ 디렉토리는 구버전 백업용, 실 운영과 무관

---

