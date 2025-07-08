import json
from datetime import datetime
import os
import time

class CrawlTimer:
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.total_requests = 0
        self.total_asins = 0
        self.success_asins = 0
        self.failure_asins = 0
        self.total_reviews = 0

    def start(self):
        self.start_time = time.time()
        print(f"[타이머][start] 크롤링 시작 시간 기록: {datetime.fromtimestamp(self.start_time).strftime('%Y-%m-%d %H:%M:%S')}")

    def stop(self):
        self.end_time = time.time()
        print(f"[타이머][stop] 크롤링 종료 시간 기록: {datetime.fromtimestamp(self.end_time).strftime('%Y-%m-%d %H:%M:%S')}, 소요 시간: {self.get_duration_str()}")

    def set_total_requests(self, count):
        self.total_requests = count

    def set_total_asins(self, total_count, success_count=0, failure_count=0):
        self.total_asins = total_count
        self.success_asins = success_count
        self.failure_asins = failure_count

    def set_total_reviews(self, count):
        self.total_reviews = count

    def get_duration_str(self):
        if not self.start_time or not self.end_time:
            return ""
        total_seconds = int(self.end_time - self.start_time)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours}시간 {minutes}분 {seconds}초"

    def save(self, file_path):
        if not self.start_time or not self.end_time:
            print("[타이머][save] 시작 또는 종료 시간이 없어 요약을 저장할 수 없습니다.")
            return

        duration_seconds = self.end_time - self.start_time
        reviews_per_sec = (self.total_reviews / duration_seconds) if duration_seconds > 0 else 0
        success_rate = (self.success_asins / self.total_asins) * 100 if self.total_asins > 0 else 0

        summary_data = {
            "StartTime": datetime.fromtimestamp(self.start_time).strftime('%Y-%m-%d %H:%M:%S'),
            "EndTime": datetime.fromtimestamp(self.end_time).strftime('%Y-%m-%d %H:%M:%S'),
            "TotalDuration": self.get_duration_str(),
            "TotalASINsProcessed": self.total_asins,
            "Success": self.success_asins,
            "Failure": self.failure_asins,
            "SuccessRate": f"{success_rate:.2f}%",
            "TotalReviewsCrawled": self.total_reviews,
            "Performance": f"{reviews_per_sec:.2f} reviews/sec"
        }

        output_dir = os.path.dirname(file_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(summary_data, f, ensure_ascii=False, indent=4)
            print(f"[타이머][save] 크롤링 요약 저장 완료: {file_path}")
        except Exception as e:
            print(f"[타이머][save] 요약 파일 저장 중 오류 발생: {e}")
        return file_path 