"""
root_logger.py
--------------

애플리케이션 전역 공통 콘솔/파일 로깅 환경 root logger 설정 클래스 모듈
"""


import logging
import sys
from pathlib import Path
from typing import ClassVar

from core.base.log.base_storage_logger import BaseStorageLogger
from core.common.log.color_formatter import ColorFormatter
from util.path_util import get_or_create_directory

from config.constant.path_constants import APPLICATION_LOG_PATH


class RootLogger(BaseStorageLogger):
    """
    애플리케이션 전역 공통 콘솔/파일 로깅 환경 root logger 설정 클래스

    주요 역할
    - root logger 초기화 및 설정
    - 콘솔 로그 출력
    - 파일 로그 save
    - logging 패키지 기반 전역 로그 환경 구성
    """

    STORAGE_PATH: ClassVar[Path] = APPLICATION_LOG_PATH

    @classmethod
    def initialize(cls) -> None:
        """
        애플리케이션 공통 전역 콘솔/파일 로깅 환경 root logger logging 객체 초기화

        주의 사항
        - 애플리케이션 시작 시점에 반드시 해당 클래스의 initialize() 호출을 권고

        :return: 없음
        """

        # 검증
        if cls._logger is not None:
            return

        if cls.STORAGE_PATH is None:
            raise ValueError(
                f"{cls.__name__} 클래스의 내부에서 관리하는 필수 변수에 대한 초기화 및 설정이 이루어지지 않았습니다. "
                "코드를 확인해주세요."
            )

        root_logger = logging.getLogger()

        # 중복 초기화 방지
        if root_logger.handlers:
            cls._logger = root_logger
            return

        root_logger.setLevel(logging.DEBUG)

        log_format = (
            "[%(levelname)s] "
            "%(asctime)s - "
            "%(name)s - "
            "%(message)s"
        )

        # 콘솔 로그 (handler)
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(logging.DEBUG)
        stream_handler.setFormatter(
            ColorFormatter(
                log_format,
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

        # 파일 로그 (handler)
        get_or_create_directory(
            full_path=cls.STORAGE_PATH.parent
        )

        file_handler = logging.FileHandler(
            cls.STORAGE_PATH,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(
            logging.Formatter(
                log_format,
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

        # 최종 설정
        root_logger.handlers.clear()

        root_logger.addHandler(stream_handler)
        root_logger.addHandler(file_handler)

        cls._logger = root_logger
