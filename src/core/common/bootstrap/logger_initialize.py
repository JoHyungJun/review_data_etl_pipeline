"""
logger_initialize.py
--------------------

애플리케이션 프로세스 실행에 요구되는 logger 관련 초기화 및 setup 모듈
"""


from core.common.log.root_logger import RootLogger
from process.core.postprocess.postprocessing.postprocessor.common.sentiment.log.model.logger.sentiment_config_tuner_statistics_meta_logger import \
    SentimentConfigTunerStatisticsMetaLogger
from process.core.postprocess.postprocessing.postprocessor.common.sentiment.log.model.logger.sentiment_inferred_logger import \
    SentimentEventLogger
from util.logging_util import logging_error_event


def initialize_logger() -> None:
    """
    애플리케이션 프로세스 실행에 요구되는 logger 관련
    초기화 및 setup 수행

    주요 역할
    - 애플리케이션 전역 공통 콘솔/파일 로깅 관련 root logger 초기화
    - 감성 추론 결과 로깅 관련 logger 초기화
    - 감성 추론 결과 로그의 통계 및 분석 로깅 관련 logger 초기화

    :return: 없음
    """

    try:
        RootLogger.initialize()
        SentimentEventLogger.initialize()
        SentimentConfigTunerStatisticsMetaLogger.initialize()

    except Exception as e:
        logging_error_event(
            exception_instance=e,
            log_message="While initializing loggers",
            log_message_detail=str(e),
            log_metadata={
                "process": "initialize_logger",
            },
        )
        raise