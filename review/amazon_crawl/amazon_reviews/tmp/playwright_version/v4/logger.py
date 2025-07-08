"""
로깅 관련 기능을 담고 있는 모듈
로깅 설정 및 인스턴스 생성을 담당합니다.
"""
import os
import sys
import time
import logging
from logging.handlers import TimedRotatingFileHandler
import config
from datetime import datetime


class SafeRotatingFileHandler(TimedRotatingFileHandler):
    """
    안전한 로그 파일 교체를 위한 핸들러
    기존 로그 파일이 존재할 경우 충돌 없이 교체합니다.
    """
    def __init__(self, filename, when='h', interval=1, backup_count=0, 
                 encoding=None, delay=False, utc=False):
        TimedRotatingFileHandler.__init__(self, filename, when, interval, 
                                         backupCount=backup_count, encoding=encoding, 
                                         delay=delay, utc=utc)

    def doRollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None
        current_time = int(time.time())
        dst_now = time.localtime(current_time)[-1]
        t = self.rolloverAt - self.interval
        if self.utc:
            time_tuple = time.gmtime(t)
        else:
            time_tuple = time.localtime(t)
            dst_then = time_tuple[-1]
            if dst_now != dst_then:
                if dst_now:
                    addend = 3600
                else:
                    addend = -3600
                time_tuple = time.localtime(t + addend)
        dfn = self.baseFilename + "." + time.strftime(self.suffix, time_tuple)
        if not os.path.exists(dfn) and os.path.exists(self.baseFilename):
            os.rename(self.baseFilename, dfn)
        if self.backupCount > 0:
            for s in self.getFilesToDelete():
                os.remove(s)
        if not self.delay:
            self.mode = "a"
            self.stream = self._open()
        new_rollover_at = self.computeRollover(current_time)
        while new_rollover_at <= current_time:
            new_rollover_at = new_rollover_at + self.interval
        self.rolloverAt = new_rollover_at


def setup_logger(name='amazon_crawler', log_level=logging.INFO):
    os.makedirs(config.LOG_DIR, exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    if logger.handlers:
        return logger
    log_format = '[%(asctime)s] [%(levelname)s] [%(module)s] [%(funcName)s] %(message)s'
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_format = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")
    console_handler.setFormatter(console_format)
    log_file_path = config.LOG_FILE_PATH
    file_handler = SafeRotatingFileHandler(
        log_file_path,
        when='midnight',
        backup_count=7,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_format = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")
    file_handler.setFormatter(file_format)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger

# logger = setup_logger()  # 이 부분은 main.py에서 직접 호출하도록 제거
