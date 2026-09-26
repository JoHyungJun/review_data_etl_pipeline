"""
review_scraping_config.py
-------------------------

A-bly 플랫폼 리뷰 스크래핑 설정 모듈

- 스크래핑 API 관련 정보 및 수집 데이터 포맷, save 경로 등의 설정값 제공
- BaseScrapConfig 를 상속받아 공통 스크래핑 API 설정 인터페이스 구현
"""


from pathlib import Path
from typing import BinaryIO, Union, Optional

from domain.platform.ably.api.format.review_scraping_format import (
    ABLY_REVIEW_SCRAPING_RESPONSE_JSON_FORMAT
)
from core.base.domain.api.base_scraping_config import BaseScrapingConfig
from domain.platform.ably.schema.review_scraping_attribute_schema import AblyReviewScrapingReviewAttributeSchema
from domain.platform.platform import Platform
from util.validate_util import (
    get_validated_date_by_str,
    get_validated_time_by_str,
    get_validated_and_parsed_unsigned_int,
    get_validated_and_parsed_float,
)


class AblyReviewScrapingConfig(BaseScrapingConfig):
    """
    A-bly 플랫폼 리뷰 스크래핑 설정 클래스

    - API 호출 정보 (API method, url, header, query params, body 등) 관리
    - 수집 시작/종료 날짜, 시간, 페이징 (per_page), token 설정
    - 스크래핑 시 재시도 횟수 (max_retries) 와 요청 간 딜레이 (delay_seconds) 설정
    - 플랫폼에서 제한한 최대 스크래핑 기한 (get_scrap_term_limit_ms) 설정
    """

    def __init__(
            self,
            token: str,
            per_page: int,
            start_date: str,
            start_time: str,
            end_date: str,
            end_time: str,
            output_directory_path: Union[str, Path, None] = None,
            max_retries: int = 3,
            delay_seconds: float = 1.0,
    ):
        self._token = token
        self._per_page = get_validated_and_parsed_unsigned_int(per_page)
        self._start_date = get_validated_date_by_str(start_date)
        self._start_time = get_validated_time_by_str(start_time)
        self._end_date = get_validated_date_by_str(end_date)
        self._end_time = get_validated_time_by_str(end_time)
        self._output_directory_path = Path(output_directory_path) if output_directory_path else None
        self._max_retries = get_validated_and_parsed_unsigned_int(max_retries)
        self._delay_seconds = get_validated_and_parsed_float(delay_seconds)

        self._platform = Platform.ABLY
        self._attribute_schema = AblyReviewScrapingReviewAttributeSchema
        self._response_json_format = ABLY_REVIEW_SCRAPING_RESPONSE_JSON_FORMAT

    def get_platform_kor_name(self) -> str:
        return self._platform.get_platform_kor_name()

    def get_platform_eng_name(self) -> str:
        return self._platform.get_platform_eng_name()

    def get_method(self) -> str:
        return "GET"

    def get_base_url(self) -> str:
        return "https://api.a-bly.com/seller/reviews"

    def get_headers(self) -> dict:
        return {
            "Authorization": self._token
        }

    def get_scraping_start_date(self) -> str:
        return self._start_date

    def get_scraping_start_time(self) -> Optional[str]:
        return self._start_time

    def get_scraping_end_date(self) -> str:
        return self._end_date

    def get_scraping_end_time(self) -> Optional[str]:
        return self._end_time

    def get_scraping_term_limit_ms(self) -> Optional[int]:
        return None

    def get_query_params(
            self,
            page: int,
            start_date: Optional[str] = None,
            start_time: Optional[str] = None,
            end_date: Optional[str] = None,
            end_time: Optional[str] = None,
    ) -> dict:
        return {
            "page": page,
            "per_page": self._per_page,
            "started_at": f"{start_date or self._start_date} {start_time or self._start_time}",
            "finished_at": f"{end_date or self._end_date} {end_time or self._end_time}",
            "order_by": "LATEST",
        }

    def get_request_payload(self) -> dict:
        return {}

    def get_request_file(self, file_name: str, file_binary: BinaryIO) -> dict:
        return {}

    def get_json_target_data_path(self) -> list[str]:
        return ["reviews"]

    def get_json_target_data_pk_name(self) -> str:
        return "sno"

    def get_api_expected_success_status_codes(self) -> set[int]:
        return {200}

    def get_json_format(self) -> dict:
        return self._response_json_format

    def _get_nested_formant_json_attribute_mapping(self) -> dict:
        return {
            self.get_json_target_data_pk_name(): self._attribute_schema.REVIEW_ID,
            "updated_at": self._attribute_schema.REVIEW_CREATED_DATETIME,
            "contents": self._attribute_schema.REVIEW_CONTENTS,
            "size": self._attribute_schema.PRODUCT_SIZE,
            "images": [self._attribute_schema.URL_IMAGE] * 10,
            "order_item_sno": self._attribute_schema.ORDER_ID,
            "goods": {
                "sno": self._attribute_schema.PRODUCT_ID,
            },
        }

    def get_max_retries(self) -> int:
        return self._max_retries

    def get_delay_seconds(self) -> float:
        return self._delay_seconds


# ===================================================
#  note
#
# - review scraping API 테스트 결과 PER_PAGE 한도는 없지만 (10000까지 테스트 결과 ok), 주말에는 10000 개씩 가능했으나, 오전엔 501 bad gateway 반환.
# - 검색 범위의 마지막 페이지가 넘어가면 멈추는 게 아니라, 마지막 페이지 데이터로 무한 응답함.
# ===================================================
