"""
name_constants.py
-----------------

프로젝트의 구조 통일, 산출물 생성/접근/저장 관리, 파이프라인 실행의 편의성 등을 위한
주요 디렉토리/파일/모듈 이름에 대한 상수 모음 모듈
"""


# ------------------------------------------
# 핵심 디렉토리 폴더 명
# ------------------------------------------

# root 폴더 명
ROOT_DIRECTORY_NAME = "review_data_etl_pipeline"

# root 하위 주요 폴더 명
SRC_DIRECTORY_NAME = "src"
DATAS_DIRECTORY_NAME = "datas"
SENTIMENT_MODEL_DIRECTORY_NAME = "sentiment_model"
CONFIG_DIRECTORY_NAME = "config"
LOGS_DIRECTORY_NAME = "logs"

SRC_CONFIG_DIRECTORY_NAME = "config"
CONFIG_CONSTANTS_DIRECTORY_NAME = "constants"


# ------------------------------------------
# 플랫폼별 상수
# ------------------------------------------

# common
COMMON_SECTION_KEY = "common"

# ably
ABLY_ENG_NAME = "A-bly"
ABLY_KOR_NAME = "에이블리"
ABLY_DIRECTORY_NAME = "ably"
ABLY_SECTION_KEY = "ably"

# coupang
COUPANG_ENG_NAME = "Coupang"
COUPANG_KOR_NAME = "쿠팡"
COUPANG_DIRECTORY_NAME = "coupang"
COUPANG_SECTION_KEY = "coupang"

# vreview
VREVIEW_ENG_NAME = "VReview"
VREVIEW_KOR_NAME = "브이리뷰"
VREVIEW_DIRECTORY_NAME = "vreview"
VREVIEW_SECTION_KEY = "vreview"


# ------------------------------------------
# 설정 관련 파일 명
# ------------------------------------------

CONFIG_INI_FILE_NAME = "config.ini"
CONFIG_SCHEMA_YML_FILE_NAME = "config_schema.yml"
SCHEMA_CONSTANTS_PY_FILE_NAME = "../../../core/config/constant/schema_constants.py"

SENTIMENT_CONFIG_JSON_FILE_NAME = "sentiment_config.json"

# reference
# vreview
VREVIEW_ID_TO_PLATFORM_ID_MAPPING_XLSX_FILE_NAME = "vreview_product_id_mapping.xlsx"
VREVIEW_ID_TO_PRODUCT_OPTION_MAPPING_XLSX_FILE_NAME = "vreview_product_option_mapping.xlsx"


# ------------------------------------------
# OUTPUT 관련 중간 산출물 파일 명
# ------------------------------------------

# output
REVIEW_SCRAPING_OUTPUT_XLSX_FILE_NAME = "review_scraping_output.xlsx"
ORDER_HISTORY_SCRAPING_OUTPUT_XLSX_FILE_NAME = "order_history_output.xlsx"
PREPROCESSING_OUTPUT_XLSX_FILE_NAME = "preprocessing_output.xlsx"
POSTPROCESSING_OUTPUT_XLSX_FILE_NAME = "postprocessing_output.xlsx"
FINALIZING_SUCCESS_OUTPUT_XLSX_FILE_NAME = "finalizing_success_output.xlsx"
FINALIZING_FAILED_OUTPUT_XLSX_FILE_NAME = "finalizing_failed_output.xlsx"


# log
# 공통 전역 로그
APP_LOG_FILE_NAME = "application.log"

# 감성 추론 로그
SENTIMENT_LOGS_DIRECTORY_NAME = "sentiment"

SENTIMENT_EVENT_LOGGER_NAME = "sentiment_event"
SENTIMENT_EVENT_LOG_JSONL_FILE_NAME = "sentiment_event.jsonl"

SENTIMENT_CONFIG_TUNER_STATISTICS_META_LOGGER_NAME = "sentiment_tuner_statistical_meta_data"
SENTIMENT_CONFIG_TUNER_STATISTICS_META_LOG_JSONL_FILE_NAME = "sentiment_tuner_statistical_meta_data.jsonl"
