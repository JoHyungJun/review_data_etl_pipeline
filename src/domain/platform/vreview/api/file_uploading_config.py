"""
file_uploading_config.py
-------------------------

VReview 플랫폼 Excel 리뷰 데이터 이관 설정 모듈

- 리뷰 이관 API 관련 정보 등의 설정값 제공
- BaseApiConfig 를 상속받아 공통 API 설정 인터페이스 구현
"""


from typing import BinaryIO, Optional

from core.base.domain.api.base_api_config import BaseApiConfig
from domain.platform.platform import Platform
from domain.platform.vreview.api.format.file_uploading_format import VREVIEW_FILE_UPLOADING_RESPONSE_JSON_FORMAT
from util.validate_util import (
    get_validated_and_parsed_unsigned_int,
    get_validated_and_parsed_float,
)


class VreviewFileUploadingConfig(BaseApiConfig):
    """
    VReview 플랫폼 Excel 리뷰 데이터 이관 설정 클래스

    - API 호출 정보 (API method, url, header, query params, body 등) 관리
    - JSON 포맷, 전송 파일의 최대 데이터 개수 (split_chunk_size) 관리
    - 파일 이관 시 재시도 횟수 (max_retries) 와 요청 간 딜레이 (delay_seconds) 설정
    """

    def __init__(
            self,
            shopping_mall_id: int,
            token: str,
            max_retries: int = 3,
            delay_seconds: float = 1.0,
    ):
        self._shopping_mall_id = get_validated_and_parsed_unsigned_int(shopping_mall_id)
        self._token = token
        self._max_retries = get_validated_and_parsed_unsigned_int(max_retries)
        self._delay_seconds = get_validated_and_parsed_float(delay_seconds)

        self._platform = Platform.VREVIEW

        self._response_json_format = VREVIEW_FILE_UPLOADING_RESPONSE_JSON_FORMAT

    def get_platform_kor_name(self) -> str:
        return self._platform.get_platform_kor_name()

    def get_platform_eng_name(self) -> str:
        return self._platform.get_platform_eng_name()

    def get_method(self) -> str:
        return "POST"

    def get_base_url(self) -> str:
        return f"https://one.vreview.tv/api/bidmin/v2/{self._shopping_mall_id}/file_ingest"

    def get_headers(self) -> dict:
        return {
            "Authorization": self._token,
            "Accept": "application/json"
        }

    def get_query_params(
            self,
            page: int,
            start_date: Optional[str] = None,
            start_time: Optional[str] = None,
            end_date: Optional[str] = None,
            end_time: Optional[str] = None,
    ) -> dict:
        return {}

    def get_request_payload(self) -> dict:
        return {}

    def get_request_file(self, file_name: str, file_binary: BinaryIO) -> dict:
        return {
            "file": (file_name, file_binary, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        }

    def get_api_expected_success_status_codes(self) -> set[int]:
        return {201}

    def get_response_json_format(self) -> dict:
        return self._response_json_format

    def get_max_retries(self) -> int:
        return self._max_retries

    def get_delay_seconds(self) -> float:
        return self._delay_seconds
