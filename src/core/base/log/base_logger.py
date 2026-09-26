"""
base_logger.py
--------------

logging 관련 공통 속성 클래스 설정 모듈
"""


import logging
from abc import ABC, abstractmethod
from typing import ClassVar, Optional


class BaseLogger(ABC):
    """
    logging 관련 공통 속성 클래스 모듈

    해당 객체는 static 한 성격으로 별도의 객체 생성 없이 class method 로 활용할 수 있지만,
    관리하는 변수들의 초기화를 위해 반드시 한 번의 initialize() 호출이 요구됨

    해당 클래스를 상속하는 로그 관련 클래스는 logging 기반으로 동작해야 하며,
    initialize() 에 logging 객체 관련 초기화, 포맷터, 파일 핸들러 등의 과정이 명시되어야 함
    """

    _logger: ClassVar[Optional[logging.Logger]] = None

    @classmethod
    @abstractmethod
    def initialize(cls, *args, **kwargs) -> None:
        """
        클래스 내부에서 관리하는 logging 객체에 대한 초기화 및 설정

        initialize 에 대한 구체적인 구현은 하위 구현체 및 인터페이스가 책임을 가짐

        :return: 없음
        """

        pass


    @classmethod
    def _is_initialized(cls) -> bool:
        return cls._logger is not None


    @classmethod
    def _validate_initialized(cls) -> None:
        """
        클래스 내부에서 관리하는 logging 객체 초기화 검증

        해당 클래스가 관리하는 변수 초기화가 이루어지지 않은 상태일 시 에러 반환

        :return: 없음
        """

        if not cls._is_initialized():
            raise ValueError(
                f"{cls.__name__} 클래스의 내부에서 관리하는 필수 변수, 혹은 logging 객체에 대한 초기화 및 설정이 이루어지지 않았습니다. "
                "코드를 확인해주세요."
            )


    @classmethod
    def get_logger(cls) -> logging.Logger:
        cls._validate_initialized()

        return cls._logger
