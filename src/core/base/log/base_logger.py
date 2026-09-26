"""
base_logger.py
--------------

logging 관련 공통 속성 클래스 설정 모듈
"""


import logging
from abc import ABC, abstractmethod
from typing import ClassVar


class BaseLogger(ABC):
    """
    logging 관련 공통 속성 클래스 모듈

    해당 객체는 static 한 성격으로 별도의 객체 생성 없이 class method 로 활용할 수 있지만,
    관리하는 변수들의 초기화를 위해 반드시 한 번의 initialize() 호출이 요구됨

    해당 클래스를 상속하는 로그 관련 클래스는 logging 기반으로 동작해야 하며,
    initialize() 에 logging 객체 관련 초기화, 포맷터, 파일 핸들러 등의 과정이 명시되어야 함
    """

    _logger: ClassVar[logging.Logger] = None

    @classmethod
    @abstractmethod
    def initialize(cls) -> None:
        """
        클래스 내부에서 관리하는 logging 객체에 대한 초기화 및 설정

        :return: 없음
        """

        pass
    
    @classmethod
    def _is_initialized(cls) -> bool:
        return cls._logger is not None

    @classmethod
    def _ensure_initialized(cls) -> None:
        """
        클래스 내부에서 관리하는 logging 객체 초기화 검증

        해당 클래스가 관리하는 변수 초기화가 이루어지지 않은 상태일 시
        자체적으로 initialize() 를 수행하고,
        그 후에도 변수가 초기화 되지 않는다면 에러 반환

        주의 사항
        - 해당 메서드는 클래스 초기화를 보장하는 역할로,
          다른 메서드의 앞단에 호출하여 초기화 에러를 방어할 것을 권장

        :return: 없음
        """

        if not cls._is_initialized():
            cls.initialize()

        if not cls._is_initialized():
            raise ValueError(
                f"{cls.__name__} 클래스의 내부에서 관리하는 필수 변수, 혹은 logging 객체에 대한 초기화 및 설정이 이루어지지 않았습니다. "
                "코드를 확인해주세요."
            )

    @classmethod
    def get_logger(cls) -> logging.Logger:
        cls._ensure_initialized()

        return cls._logger
