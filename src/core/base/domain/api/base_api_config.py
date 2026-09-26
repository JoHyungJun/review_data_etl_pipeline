"""
base_api_config.py
------------------

API 관련 정보 관리의 기반이 되는 추상 클래스 설정 모듈

- API 관련 필수 공통 값 강제
"""


from abc import ABC, abstractmethod
from typing import BinaryIO, Optional


class BaseApiConfig(ABC):
    """
    API 관련 정보 관리의 기반 설정 추상 클래스

    - API 호출 정보 (API method, url, header, query params, body 등) 구현 강제
    - API 반복 요청 시 재시도 횟수 (max_retries) 와 요청 간 딜레이 (delay_seconds) 설정 강제
    """

    @abstractmethod
    def get_platform_kor_name(self) -> str:
        pass

    @abstractmethod
    def get_platform_eng_name(self) -> str:
        pass

    @abstractmethod
    def get_method(self) -> str:
        pass

    @abstractmethod
    def get_base_url(self) -> str:
        pass

    @abstractmethod
    def get_headers(self) -> dict:
        pass

    @abstractmethod
    def get_query_params(
            self,
            page: int,
            start_date: Optional[str] = None,
            start_time: Optional[str] = None,
            end_date: Optional[str] = None,
            end_time: Optional[str] = None,
    ) -> dict:
        pass

    @abstractmethod
    def get_request_payload(self, *args, **kwargs) -> dict:
        pass

    @abstractmethod
    def get_request_file(self, file_name: str, file_binary: BinaryIO) -> dict:
        pass

    @abstractmethod
    def get_api_expected_success_status_codes(self) -> set[int]:
        pass

    @abstractmethod
    def get_max_retries(self) -> int:
        pass

    @abstractmethod
    def get_delay_seconds(self) -> float:
        pass
