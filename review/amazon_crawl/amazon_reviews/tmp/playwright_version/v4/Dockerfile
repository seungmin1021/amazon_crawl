# 1. Python 3.11 slim 기반
FROM python:3.11-slim

# 2. 필수 패키지 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl wget git unzip \
        fonts-nanum fonts-liberation \
        libnss3 libatk-bridge2.0-0 libgtk-3-0 libxss1 libasound2 libgbm1 libxshmfence1 libu2f-udev libvulkan1 ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Firefox 및 geckodriver 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        firefox-esr \
        wget \
        fonts-nanum fonts-liberation \
        libnss3 libatk-bridge2.0-0 libgtk-3-0 libxss1 libasound2 libgbm1 libxshmfence1 libu2f-udev libvulkan1 ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN wget -qO- https://github.com/mozilla/geckodriver/releases/download/v0.36.0/geckodriver-v0.36.0-linux64.tar.gz | tar xz -C /usr/local/bin

# 3. 작업 디렉토리 및 소스 복사
WORKDIR /app
COPY . /app

# 4. 파이썬 패키지 설치
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 5. Playwright 브라우저 바이너리 설치
RUN pip install --no-cache-dir playwright && \
    playwright install --with-deps

# 6. 한글 폰트/로케일 설정 (필요시)
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# 7. ENTRYPOINT, CMD 설정
ENTRYPOINT ["python", "main.py"]
CMD ["--login_browser", "firefox", "--login_headless", "--crawling_headless", "--use_proxy", "--max_pages", "10", "--max_concurrent_contexts", "10", "--asin_start", "0", "--log_level", "DEBUG"]