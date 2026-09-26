"""
sentiment_model_initialize.py
-----------------------------

애플리케이션 프로세스 실행에 요구되는 감성 추론 모델 설정 관련 초기화 및 setup 모듈
"""


from pathlib import Path
from typing import Union

from process.core.postprocess.postprocessing.postprocessor.common.sentiment.config.sentiment_config import \
    SentimentConfig
from process.core.postprocess.postprocessing.postprocessor.common.sentiment.model.sentiment_model import SentimentModel
from util.logging_util import logging_error_event


def initialize_sentiment_model(sentiment_model_path: Union[Path, str]) -> None:
    """
    애플리케이션 프로세스 실행에 요구되는 감성 추론 모델 설정 관련
    초기화 및 setup 수행

    주요 역할
    - 감성 추론 모델 정적 설정 정보 관리 sentiment config 초기화
    - 감성 추론 모델 관리 sentiment model 초기화

    :param sentiment_model_path: 감성 추론 모델이 위치하는 디렉토리 경로 Union[Path, str]
    :return: 없음
    """

    try:
        sentiment_config = SentimentConfig.load()
        SentimentModel.initialize_sentiment_model(
            model_path=sentiment_model_path,
            sentiment_config=sentiment_config,
        )

    except Exception as e:
        logging_error_event(
            exception_instance=e,
            log_message="While initializing sentiment model/config",
            log_message_detail=str(e),
            log_metadata={
                "process": "initialize_sentiment_model",
            },
        )
        raise