#!/bin/bash

# 사용법:
#   bash run_crawler.sh [python main.py에 넘길 인자들]
# 예시:
#   bash run_crawler.sh --browser firefox --use_proxy --asin_start 0 --asin_end 20 --max_pages 10
#   bash run_crawler.sh --browser chrome --headless

# 1. 모든 프로세스 종료 및 lock 파일 삭제
killall Xvfb 2>/dev/null
killall x11vnc 2>/dev/null
killall firefox 2>/dev/null
rm -f /tmp/.X99-lock

# 2. Xvfb 실행 및 DISPLAY 환경변수 설정
Xvfb :99 -screen 0 1920x1080x24 &
sleep 2
export DISPLAY=:99

# 3. x11vnc 실행
x11vnc -display :99 -nopw -listen localhost -xkb &
sleep 2

# 4. VNC 뷰어를 또 다른 터미널에서 실행 (필요시)
gnome-terminal -- bash -c "vncviewer localhost:5900; exec bash"

# 5. 크롤러를 또 다른 터미널에서 실행 (가상환경 활성화 후 python main.py)
gnome-terminal -- bash -c "cd $(pwd); source ~/anaconda3/etc/profile.d/conda.sh; conda activate amz_crw_scr; python main.py $*; exec bash"

# 참고:
# - VNC 뷰어(vncviewer)는 필요할 때만 사용하세요. (GUI로 브라우저를 보고 싶을 때)
# - python main.py 실행 인자는 run_crawler.sh 실행 시 자유롭게 입력하세요. 