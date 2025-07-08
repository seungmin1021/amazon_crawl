# Amazon Login Only (Selenium)

- 프로필 경로 지정을 통한 VPN 구현 (But, VPN 아이디/비밀번호 요구로 이를 무시하며 진행)
- Selenium 기반 로그인
- Scrapy 기반 크롤링
- Free Proxy 성공

### 실행 명령어

#### 기본 

```bash
sudo apt install xvfb
xvfb-run -a python main.py
```

```bash
python main.py --headless
```

#### 프록시 실행 시

```bash
python main.py --headless --use_proxy
```
#### CAPTCHA 수동 해결 방식

```bash
# Xvfb 설치
sudo apt update
sudo apt install xvfb x11vnc
```

```bash
# Xvfb로 가상 디스플레이 실행
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99
```

```bash
# 크롤링 실행
# CAPTCHA 발생 시, 직접 해결후 크롤링 진행
x11vnc -display :99 -nopw -listen localhost -xkb & python main.py
```


#### CAPTCHA 수동 해결 방식(2)

```bash
# 1. 모든 프로세스 종료 및 lock 파일 삭제
killall Xvfb
killall x11vnc
killall firefox
rm -f /tmp/.X99-lock
# 2. Xvfb 실행 3. DISPLAY 환경변수 설정
Xvfb :99 -screen 0 1920x1080x24 & export DISPLAY=:99
export DISPLAY=:99
# 4. x11vnc 실행
x11vnc -display :99 -nopw -listen localhost -xkb &

# 5. VNC 뷰어 실행 (다른 터미널에서)
vncviewer localhost:5900
# 6. 크롤러 실행 (다른 터미널에서, export DISPLAY=:99 한 후)
python main.py
```

#### run_crawler.sh 활용 실행 방식

```bash
# 설치
sudo apt update
sudo apt install gnome-terminal

# 실행 권한
chmod +x run_crawler.sh
```

```bash
# Firefox, 프록시 사용, 0~20번 ASIN, 최대 10페이지 크롤링
bash run_crawler.sh --use_proxy --asin_start 0 --asin_end 20 --max_pages 3
bash run_crawler.sh --browser firefox --use_proxy --asin_start 0 --asin_end 20 --max_pages 10
# Chrome, headless, 전체 ASIN
bash run_crawler.sh --browser chrome --headless
```

#### headless로 실행

```bash
python main.py --headless --use_proxy --asin_start 0 --asin_end 20 --max_pages 3
```

#### Playwright v2 실행

```bash
python main.py --login_browser firefox --login_headless --crawling_headless --use_proxy --asin_start 0 --asin_end 30 --max_pages 3 --max_concurrent_contexts 5 --log_level DEBUG
```


# 프록시 무료 발급

[https://free-proxy-list.net/](https://free-proxy-list.net/)

# 동적 요청

```text
# requirements.txt 추가
pip install scrapy-playwright playwright
playwright install firefox
```

```bash
playwright install
```
