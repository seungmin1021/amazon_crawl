import json
from datetime import datetime, timedelta
import os

class CrawlTimer:
    def __init__(self, result_json_path):
        self.result_json_path = result_json_path
        self.start_time = None
        self.end_time = None
        self.elapsed = None
        self.total_requests = 0
        self.total_asins = 0
        self.total_reviews = 0

    def start(self):
        self.start_time = datetime.now()
        print("[타이머][start] 크롤링 시작 시간 기록:", self.start_time)

    def stop(self):
        self.end_time = datetime.now()
        self.elapsed = self.end_time - self.start_time if self.start_time and self.end_time else None
        print("[타이머][stop] 크롤링 종료 시간 기록:", self.end_time, "소요 시간:", self.get_elapsed_str())

    def set_total_requests(self, n):
        self.total_requests = n

    def set_total_asins(self, n):
        self.total_asins = n

    def set_total_reviews(self, n):
        self.total_reviews = n

    def get_elapsed_str(self):
        if not self.elapsed:
            return ""
        total_seconds = int(self.elapsed.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours}시간{minutes}분{seconds}초"

    def get_timer_json_path(self):
        base, ext = os.path.splitext(self.result_json_path)
        return f"{base}_timer.json"

    def save(self):
        timer_data = {
            "start_time": self.start_time.strftime("%Y-%m-%d %H:%M:%S") if self.start_time else None,
            "end_time": self.end_time.strftime("%Y-%m-%d %H:%M:%S") if self.end_time else None,
            "elapsed": self.get_elapsed_str(),
            "total_asins": self.total_asins,
            "total_requests": self.total_requests,
            "total_reviews": self.total_reviews
        }
        timer_json_path = self.get_timer_json_path()
        output_dir = os.path.dirname(timer_json_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        with open(timer_json_path, "w", encoding="utf-8") as f:
            json.dump(timer_data, f, ensure_ascii=False, indent=4)
        print(f"[타이머][save] 타이머/통계 정보 저장 완료: {timer_json_path}")
        return timer_json_path 