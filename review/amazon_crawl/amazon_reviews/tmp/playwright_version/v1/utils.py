from selenium.webdriver.support.ui import WebDriverWait
import os
import pandas as pd
from logger import logger
import json
from datetime import datetime
from config import RESULTS_PATH

def wait_for_page_load(driver, timeout=30):
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script('return document.readyState') == 'complete'
    )
    logger.debug("[유틸][wait_for_page_load] 페이지 로드 완료")

def load_asin_info_from_excel(excel_path, sheet_name):
    """
    엑셀에서 ASIN 및 메타데이터 컬럼을 모두 dict로 반환
    """
    logger.info(f"[유틸][load_asin_info_from_excel] 엑셀 파일 로드 시도: {excel_path}, 시트: {sheet_name}")
    try:
        if not os.path.exists(excel_path):
            logger.error(f"[로드] ASIN 엑셀 파일을 찾을 수 없습니다: {excel_path}")
            return []
        df = pd.read_excel(excel_path, sheet_name=sheet_name)

        # 필요한 컬럼명
        required_cols = ["DATA_GBN", "LAST_CRAWL_DTTM", "ASIN", "FIRST_DTTM", "URL"]
        # 컬럼명 대소문자 무시 매핑
        col_map = {col.lower(): col for col in df.columns}
        for req in required_cols:
            if req.lower() not in col_map:
                logger.error(f"[로드] 엑셀 파일에 '{req}' 컬럼이 없습니다: {excel_path}")
                return []
        # 날짜 컬럼을 문자열로 변환
        for date_col in ["LAST_CRAWL_DTTM", "FIRST_DTTM"]:
            col_real = col_map[date_col.lower()]
            df[col_real] = df[col_real].apply(
                lambda x: x.strftime("%Y-%m-%d") if pd.notnull(x) and hasattr(x, "strftime") else (str(x) if pd.notnull(x) else "")
            )
        # 필요한 컬럼만 추출해서 dict 리스트로 반환
        asin_list = df[[col_map[c.lower()] for c in required_cols]].dropna(subset=[col_map["asin"]])
        result = asin_list.to_dict(orient="records")
        logger.info(f"[로드] 엑셀에서 {len(result)}개의 ASIN 및 메타데이터를 로드했습니다.")
        return result
    except Exception as e:
        logger.error(f"[로드] 엑셀에서 ASIN 목록 로드 중 오류 발생: {str(e)}")
        return []

def save_results_to_json(results, filename=None):
    """
    결과 데이터를 JSON 파일로 저장합니다.
    """
    logger.info(f"[유틸][save_results_to_json] 결과 저장 시도")
    try:
        output_dir = os.path.dirname(RESULTS_PATH)
        os.makedirs(output_dir, exist_ok=True)
        file_path = filename if filename else RESULTS_PATH
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
        logger.info(f"[저장] 결과 데이터를 저장했습니다: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"[저장] 결과 저장 중 오류 발생: {str(e)}")
        return None
    
def save_failed_asin(asin, error, failure_type, failed_list, output_path):
    logger.info(f"[유틸][save_failed_asin] 실패 ASIN 저장 시도: {asin}, 사유: {error}, 타입: {failure_type}")
    # 1. 디렉토리 자동 생성
    dir_path = os.path.dirname(output_path)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)
    # 2. 실패 정보 append
    if asin is not None:
        failed_list.append({
            "ASIN": asin,
            "error": error,
            "failure_type": failure_type,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    # 3. 파일 저장
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(failed_list, f, ensure_ascii=False, indent=2)
    logger.info(f"[저장][save_failed_asin] 실패 ASIN 정보 저장 완료: {output_path}")