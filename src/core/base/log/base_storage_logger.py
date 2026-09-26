"""
base_storage_logger.py
----------------------

logging 및 로그 내용을 저장하는 logger 관련 공통 속성 클래스 설정 모듈
"""


from abc import abstractmethod
from pathlib import Path
from typing import ClassVar, Optional

from core.base.log.base_logger import BaseLogger


class BaseStorageLogger(BaseLogger):
    """
    logging 및 로그 내용을 저장하는 logger 관련 공통 속성 클래스 모듈

    해당 객체는 static 한 성격으로 별도의 객체 생성 없이 class method 로 활용할 수 있지만,
    관리하는 변수들의 초기화를 위해 반드시 한 번의 initialize() 호출이 요구됨

    해당 클래스를 상속하는 로그 관련 클래스는 logging 기반으로 동작해야 하며,
    initialize() 에 logging 객체 관련 초기화, 포맷터, 파일 핸들러 등의 과정이 명시되어야 함

    주의 사항
    - 클래스 내부에서 관리되는 logger name, log path 정보는 initialize() 내부, 혹은 클래스 선언 시점에서의 초기화를 강제
    - logger name 정보에 대한 정의는 Optional, storage path 정보에 대한 정의는 Required
    """

    LOGGER_NAME: ClassVar[Optional[str]] = None
    STORAGE_PATH: ClassVar[Optional[Path]] = None

    @classmethod
    @abstractmethod
    def initialize(cls) -> None:
        """
        클래스 내부에서 관리하는 변수 및 logging 객체에 대한 초기화 및 설정

        :return: 없음
        """

        pass

    @classmethod
    def _is_initialized(cls) -> bool:
        return (
            super()._is_initialized()
            and cls.STORAGE_PATH is not None
        )

    @classmethod
    def get_storage_path(cls) -> Optional[Path]:
        return cls.STORAGE_PATH
