"""
sentiment_inferred_logger.py
----------------------------

감성 추론 결과 로깅 관련 정보 관리 클래스 모듈
"""


from config.constant.name_constants import SENTIMENT_INFERRED_LOGGER_NAME
from config.constant.path_constants import SENTIMENT_INFERRED_JSONL_PATH
from process.core.postprocess.postprocessing.postprocessor.common.sentiment.log.model.logger.base_sentiment_jsonl_logger import \
    BaseSentimentJsonlLogger


class SentimentEventLogger(BaseSentimentJsonlLogger):
    """
    감성 추론 결과 로깅 관련 정보 관리 클래스

    주요 역할
    - 감성 추론 로그 경로 관련 정보 관리
    - 감성 추론 로그 작성 기능 제공

    해당 클래스를 상속하는 로그 관련 클래스는 logging 기반으로 동작해야 하며,
    initialize() 에 logging 객체 관련 초기화, 포맷터, 파일 핸들러 등의 과정이 명시되어야 함
    """

    LOGGER_NAME = SENTIMENT_INFERRED_LOGGER_NAME
    STORAGE_PATH = SENTIMENT_INFERRED_JSONL_PATH
