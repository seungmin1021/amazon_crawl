# Amazon Product Review Crawler (Playwright + Selenium)

## 프로젝트 개요

이 프로젝트는 아마존(amazon.com) 제품의 리뷰 데이터를 **대량/자동/병렬**로 수집하는 크롤러입니다.  
Selenium을 활용한 로그인 세션 확보와, Playwright 기반의 비동기 병렬 크롤링을 결합하여  
**안정적이고 빠른 리뷰 수집**을 지원합니다.  
엑셀로 ASIN 목록을 관리하며, robust한 예외처리, 상세한 로깅, CAPTCHA/프록시/VPN 환경까지 대응합니다.

---

## 전체 구조 및 동작 흐름

### 1. 로그인 단계 (Selenium)
- 다양한 계정(.env로 관리) 중 랜덤으로 하나를 선택해 아마존에 로그인합니다.
- 프록시/VPN을 사용할 수 있습니다.
- 로그인 성공 시, 세션 쿠키를 Playwright로 전달합니다.
- CAPTCHA, 전화번호 추가, 2차 인증 등 다양한 예외상황을 robust하게 처리합니다.

### 2. ASIN 목록 로드
- 엑셀 파일(`./data/ASIN/amazon_review_open_YYYYMMDD.xlsx`)에서 크롤링 대상 ASIN 및 메타데이터를 읽어옵니다.
- 슬라이싱 옵션으로 원하는 범위만 선택적으로 크롤링할 수 있습니다.

### 3. 리뷰 크롤링 (Playwright)
- Playwright의 비동기/병렬 기능을 활용해 여러 ASIN을 동시에 빠르게 크롤링합니다.
- 각 리뷰의 제목, 본문, 평점, 작성자, 날짜, 옵션, 인증여부, helpful vote 등 다양한 정보를 selector 기반으로 추출합니다.
- config.py에서 selector를 관리하여, 아마존 UI 변경에도 유연하게 대응할 수 있습니다.

### 4. 결과 저장 및 로깅
- 크롤링 성공/실패 결과를 각각 JSON 파일로 저장합니다.
- 크롤링 요약(성공/실패/속도 등)은 별도 timer JSON으로 저장합니다.
- 상세한 로그는 logs/ 디렉토리에 남깁니다.

---

## 설치 및 환경 셋팅

### 1. Python 환경 준비
- Python 3.8 이상 권장
- 가상환경(venv, conda 등) 사용 권장

### 2. 필수 패키지 설치

```bash
pip install -r requirements.txt
```
> `requirements.txt`에는 selenium, selenium-wire, playwright, pandas, openpyxl, numpy, requests, blinker==1.4 등 필수 패키지만 포함되어 있습니다.

### 3. Playwright 브라우저 바이너리 설치

```bash
playwright install
```
> **반드시 위 명령어를 실행해야 Playwright가 크롬/파이어폭스/웹킷 브라우저를 자동으로 설치합니다.**

### 4. 환경 변수 및 계정 설정
- `.env` 파일에 아마존 계정 정보를 아래와 같이 입력하세요:
```
AMAZON_ACCOUNTS=이메일1::비번1,이메일2::비번2
PROXIES=프록시1,프록시2 (옵션)
```
- 엑셀 파일(`./data/ASIN/amazon_review_open_YYYYMMDD.xlsx`)에 크롤링할 ASIN 목록을 준비하세요.

### Docker로 빌드 및 실행하기

#### 1. Docker 이미지 빌드

```bash
docker build -t amazon-crawler:v3 .
docker build -t pw:v3 -f Dockerfile . 2>&1 | tee pw.v3.build.log
```
- 현재 디렉토리(`amazon_reviews/playwright_version/v3`)에서 실행하세요.
- Dockerfile, main.py, requirements.txt 등 모든 소스가 이 폴더에 있어야 합니다.

#### 2. Docker 컨테이너 실행 예시

##### (1) 기본 실행 (CMD의 모든 기본값 사용)
```bash
docker run --rm amazon-crawler:v3
```
- Dockerfile의 CMD에 명시된 인자(default)로 main.py가 실행됩니다.

##### (2) 일부 인자만 직접 지정 (나머지는 main.py의 default 사용)
```bash
docker run --rm amazon-crawler:v3 --asin_start 10 --asin_end 20
```
- main.py에는 `--asin_start 10 --asin_end 20`만 전달되고, 나머지 인자는 main.py의 default 값이 적용됩니다.

##### (3) 모든 인자 직접 지정 (완전 커스텀 실행)
```bash
docker run --rm amazon-crawler:v3 --login_browser chrome --login_headless --crawling_headless --use_proxy --max_pages 5 --max_concurrent_contexts 3 --asin_start 0 --asin_end 50 --log_level INFO
```
- main.py에 입력한 인자만 전달되며, Dockerfile CMD는 무시됩니다.

##### (4) 데이터/로그/.env 볼륨 마운트 (외부 파일 사용)
```bash
docker run --rm \
  -v $PWD/data:/app/data \
  -v $PWD/logs:/app/logs \
  -v $PWD/html:/app/html \
  -v $PWD/.env:/app/.env \
  amazon-crawler:v3
```

```bash
docker run --rm ^
  -v $PWD/data:/app/data ^
  -v $PWD/logs:/app/logs ^
  -v $PWD/html:/app/html ^
  -v $PWD/.env:/app/.env ^
  pw:v3 ^
  --login_browser firefox ^
  --login_headless ^
  --crawling_headless ^
  --use_proxy ^
  --max_pages 3 ^
  --max_concurrent_contexts 10 ^
  --asin_start 0 ^
  --asin_end 50 ^
  --log_level DEBUG
```

- 컨테이너 내부 `/app/data`, `/app/logs`, `/app/.env`에 로컬 파일/폴더를 연결합니다.
- 크롤링 결과, 로그, 환경변수 파일이 호스트에 저장됩니다.

##### (5) 백그라운드 실행
```bash
docker run -d --name amazon-crawler amazon-crawler:v3
```
- 컨테이너가 백그라운드에서 실행됩니다.
- 로그는 `docker logs amazon-crawler`로 확인할 수 있습니다.

##### (6) 종료된 컨테이너/이미지 삭제
```bash
docker container prune   # 모든 종료된 컨테이너 삭제
docker rmi amazon-crawler:v3  # 이미지 삭제
```

#### 3. 추가 팁
- Dockerfile의 ENTRYPOINT, CMD 구조상 docker run 뒤에 인자를 직접 주면 CMD는 무시되고, main.py의 default 값이 적용됩니다.
- 볼륨 마운트로 data, logs, .env를 외부에 저장하는 것을 권장합니다.
- 환경변수는 -e 옵션으로도 전달할 수 있습니다.
- 컨테이너 실행 후 필요시 `docker ps -a`, `docker rm [ID]` 등으로 관리하세요.

---

## 주요 특징

- **Selenium + Playwright 하이브리드**: 로그인은 Selenium, 리뷰 크롤링은 Playwright(비동기/병렬)로 처리
- **엑셀 기반 ASIN 관리**: 엑셀에서 ASIN 및 메타데이터를 읽어와 자동 처리
- **프록시/VPN/다중계정 지원**: 프록시, VPN, 여러 계정 랜덤 선택 가능
- **CAPTCHA/전화번호 추가/2차 인증 등 robust 대응**
- **실패/성공/진행상황 상세 로깅 및 요약**
- **결과물 자동 JSON 저장, 실패 ASIN 별도 저장**
- **다양한 실행 옵션 지원 (headless, 병렬 context, 페이지 수, 슬라이싱 등)**
- **코드 구조가 명확하게 분리되어 유지보수/확장 용이**

---

## 파일/모듈별 역할

- **main.py**: 전체 실행 진입점. 인자 파싱, 환경설정, 로그인, 크롤링, 결과 저장, 로그 관리 등 전체 파이프라인 제어.
- **config.py**: 크롤링에 필요한 selector, 경로, 파일명, delay, 실패 메시지 등 각종 설정값 관리. 환경변수(.env) 연동.
- **browser.py**: Selenium/Selenium-wire 기반 브라우저 및 프록시 세팅, User-Agent 랜덤화 등.
- **login.py**: 아마존 로그인 처리, CAPTCHA/전화번호/2차 인증 robust 대응, 예외처리.
- **crawler.py**: Playwright 기반의 실제 리뷰 크롤링 로직. 비동기적으로 여러 ASIN을 병렬 처리.
- **extractors_playwright.py**: Playwright로부터 각종 리뷰 정보(제목, 본문, 평점 등)를 selector 기반으로 추출하는 함수 모음.
- **utils.py**: ASIN 목록 엑셀 로드, 결과/실패 저장, 기타 유틸리티 함수.
- **timer.py**: 크롤링 시작/종료 시간, 처리 속도, 성공/실패 건수 등 성능 측정 및 요약 저장.
- **logger.py**: 로그 파일 관리 및 설정.

---

## 사용법

### 1. 기본 실행 예시

```bash
python main.py --login_browser firefox --login_headless --crawling_headless --use_proxy --asin_start 0 --asin_end 30 --max_pages 3 --max_concurrent_contexts 5 --log_level DEBUG
```

#### 주요 옵션 설명
- `--login_browser`: 로그인에 사용할 브라우저 (firefox/chrome)
- `--login_headless`: 로그인 단계에서 headless 모드 사용
- `--crawling_headless`: 리뷰 크롤링 단계에서 headless 모드 사용
- `--use_proxy`: 프록시 사용 여부
- `--asin_start`, `--asin_end`: 엑셀에서 ASIN 슬라이싱 범위 지정
- `--max_pages`: 각 상품별 최대 크롤링 페이지 수
- `--max_concurrent_contexts`: Playwright 동시 context 개수(병렬성)
- `--log_level`: 로그 레벨 (DEBUG/INFO 등)

### 2. 다양한 실행 예시

#### (1) 크롬 브라우저, 프록시 미사용, 100개 ASIN, 5페이지씩 크롤링
```bash
python main.py --login_browser chrome --asin_start 0 --asin_end 100 --max_pages 5 --max_concurrent_contexts 3 --log_level INFO
```

#### (2) headless 해제(실제 브라우저 창 확인), 10개만 테스트
```bash
python main.py --login_browser firefox --asin_start 0 --asin_end 10 --max_pages 2 --login_headless --crawling_headless
```

#### (3) 프록시 사용, 로그 레벨 WARNING
```bash
python main.py --use_proxy --log_level WARNING
```

#### (4) headless 모드 실행 예시

```bash
# headless True (브라우저 창이 보이지 않음, Docker 컨테이너에서는 반드시 headless 모드로 실행해야 함)
python main.py --login_browser firefox --login_headless --crawling_headless --use_proxy --asin_start 0 --asin_end 10 --max_pages 3 --max_concurrent_contexts 5 --log_level DEBUG
```

```bash
# headless False (브라우저 창이 실제로 보임, 단 Docker 컨테이너에서는 실행되지 않음)
python main.py --login_browser firefox --use_proxy --asin_start 0 --asin_end 10 --max_pages 3 --max_concurrent_contexts 5 --log_level DEBUG
```

> **설명:**
> - `--login_headless`, `--crawling_headless` 인자를 주면 각각 headless 모드가 활성화됩니다.
> - 인자를 생략하면 해당 단계는 브라우저 창이 실제로 보입니다.

---

## CAPTCHA 수동 해결 방식

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
python main.py
```

> **설명:**
> - Xvfb로 가상 디스플레이를 띄우고, x11vnc로 원격 접속 가능하게 만든 뒤, VNC 뷰어로 직접 브라우저를 조작해 CAPTCHA를 수동으로 풀 수 있습니다.

---

## 저장 결과물 및 파일 구조

- `data/results/ASIN_REVIEWS_Excel_YYYYMMDDHHMMSS.json` : 크롤링된 리뷰 전체 결과 (JSON)
- `data/failed/failed_ASIN_list_YYYYMMDDHHMMSS.json` : 실패한 ASIN 및 사유 (JSON)
- `data/results/ASIN_REVIEWS_Excel_YYYYMMDDHHMMSS_timer.json` : 크롤링 요약/성능 (JSON)
- `logs/amazon_crawler_YYYYMMDD_HHMMSS.log` : 상세 로그 파일
- `html/` : 디버깅용 HTML 저장

### 결과 JSON 예시
```json
[
  {
    "DATA_GBN": "...",
    "LAST_CRAWL_DTTM": "...",
    "ASIN": "B0XXXXXXX",
    "FIRST_DTTM": "...",
    "URL": "...",
    "remain_count": 0,
    "has_next": 0,
    "total_count": 0,
    "result": [
      {
        "title": "...",
        "review_url": "...",
        "content": "...",
        "star": 5,
        "writer_nm": "...",
        "write_dt": "2024-05-09",
        "option": "...",
        "is_verified": true,
        "helpful": 3,
        "crawl_date": "2024-05-09",
        "crawl_datetime": "2024-05-09 12:34:56",
        "group_id": "B0XXXXXXX"
      },
      ...
    ],
    "crawl_review_cnt": 20
  },
  ...
]
```

---

## 고급 활용/운영 팁

- **실패/예외 케이스 자동 분류**: 상품 없음, 리뷰 없음, 네트워크 오류 등 다양한 실패 케이스를 구분하여 기록합니다.
- **엑셀 컬럼 자동 매핑**: 엑셀 컬럼명이 달라도 자동으로 매핑하여 유연하게 동작합니다.
- **로그/타이머/진행률**: 상세 로그와 타이머로 크롤링 현황 및 성능을 실시간 모니터링할 수 있습니다.
- **환경별 확장성**: config.py에서 selector, 경로, 옵션을 쉽게 수정할 수 있어, 아마존 UI 변경에도 빠르게 대응 가능합니다.
- **보안/운영**: 계정/프록시 정보는 .env로 분리 관리, 로그/결과물은 자동으로 날짜별로 분리 저장됩니다.

---

## FAQ & 참고사항

- **윈도우/리눅스/맥 모두 지원** (단, Xvfb/x11vnc는 리눅스 환경)
- **엑셀 파일은 openpyxl 필요** (`pip install openpyxl`)
- **프록시/VPN/다중계정은 .env로 관리**
- **로그인 실패/리뷰 없음/상품 없음 등 다양한 실패 케이스 자동 분류 및 기록**
- **실행 전 반드시 `playwright install` 명령을 한 번 실행해야 함**
- **실행 중 에러/로그는 logs/ 디렉토리에서 확인**
- **코드 구조가 명확하게 분리되어 있어 유지보수/확장에 매우 용이**

---

## 개발/기여 안내

- 코드 구조는 main.py(실행), config.py(설정), browser.py(드라이버), login.py(로그인), crawler.py(크롤링), extractors_playwright.py(파싱), utils.py(유틸), timer.py(성능), logger.py(로깅) 등으로 분리되어 있습니다.
- PR/이슈/기여 환영합니다.

---

## 문의

- 개발/사용 중 궁금한 점은 이슈 또는 이메일로 문의해 주세요.

---

**이 프로젝트는 실제 대규모 데이터 수집, AI/ML 데이터셋 구축, 제품/브랜드 모니터링, 시장조사 등 다양한 목적에 활용할 수 있습니다.  
코드 구조와 옵션, 예외처리, 결과물 포맷까지 꼼꼼하게 설계되어 있어,  
누구나 쉽게 확장/운영/유지보수할 수 있습니다.**
