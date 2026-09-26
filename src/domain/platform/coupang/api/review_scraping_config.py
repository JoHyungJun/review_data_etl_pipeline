"""
review_scraping_config.py
-------------------------

Coupang 플랫폼 리뷰 스크래핑 설정 모듈

- 스크래핑 API 관련 정보 및 수집 데이터 포맷, save 경로 등의 설정값 제공
- BaseScrapConfig 를 상속받아 공통 스크래핑 API 설정 인터페이스 구현
"""


from pathlib import Path
from typing import Union, Optional, BinaryIO

from core.base.domain.api.base_scraping_config import BaseScrapingConfig
from domain.platform.coupang.api.format.review_scraping_format import COUPANG_REVIEW_SCRAPING_RESPONSE_JSON_FORMAT
from domain.platform.coupang.schema.review_scraping_attribute_schema import CoupangReviewScrapingReviewAttributeSchema
from domain.platform.platform import Platform
from util.datetime_util import DAY_MILLISECONDS
from util.validate_util import (
    get_validated_and_parsed_unsigned_int,
    get_validated_date_by_str,
    get_validated_and_parsed_float,
)


class CoupangReviewScrapingConfig(BaseScrapingConfig):
    """
    Coupang 플랫폼 리뷰 스크래핑 설정 클래스

    - API 호출 정보 (API method, url, header, query params, body 등) 관리
    - 수집 시작/종료 날짜, 페이징 (per_page), cookie 설정
    - 스크래핑 시 재시도 횟수 (max_retries) 와 요청 간 딜레이 (delay_seconds) 설정
    """

    def __init__(
            self,
            cookie: str,
            per_page: int,
            start_date: str,
            end_date: str,
            output_directory_path: Optional[Union[Path, str]] = None,
            max_retries: int = 3,
            delay_seconds: float = 1.0,
    ):
        self._cookie = cookie
        self._per_page = get_validated_and_parsed_unsigned_int(per_page)
        self._start_date = get_validated_date_by_str(start_date)
        self._end_date = get_validated_date_by_str(end_date)
        self._output_directory_path = Path(output_directory_path) if output_directory_path else None
        self._max_retries = get_validated_and_parsed_unsigned_int(max_retries)
        self._delay_seconds = get_validated_and_parsed_float(delay_seconds)

        self._platform = Platform.COUPANG
        self._attribute_schema = CoupangReviewScrapingReviewAttributeSchema
        self._response_json_format = COUPANG_REVIEW_SCRAPING_RESPONSE_JSON_FORMAT

    def get_platform_kor_name(self) -> str:
        return self._platform.get_platform_kor_name()

    def get_platform_eng_name(self) -> str:
        return self._platform.get_platform_eng_name()

    def get_method(self) -> str:
        return "GET"

    def get_base_url(self) -> str:
        return "https://wing.coupang.com/tenants/cs/product/review/search"

    def get_headers(self) -> dict:
        return {
            "User_Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/115.0.0.0 "
                "Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://wing.coupang.com/tenants/cs/product/review",
            "Cookie": self._cookie,
        }

    def get_scraping_start_date(self) -> str:
        return self._start_date

    def get_scraping_start_time(self) -> Optional[str]:
        return None

    def get_scraping_end_date(self) -> str:
        return self._end_date

    def get_scraping_end_time(self) -> Optional[str]:
        return None

    def get_scraping_term_limit_ms(self) -> Optional[int]:
        return 30 * DAY_MILLISECONDS

    def get_query_params(
            self,
            page: int,
            start_date: Optional[str] = None,
            start_time: Optional[str] = None,
            end_date: Optional[str] = None,
            end_time: Optional[str] = None,
    ) -> dict:
        return {
            "startTime": start_date or self._start_date,
            "endTime": end_date or self._end_date,
            "pageIndex": page,
            "pageSize": self._per_page,
            # "rating": "",
            # "salesStatus": "true",
            # "advancedType": "productName",
            # "advancedInput": "",
            # "productName": "",
        }

    def get_request_payload(self) -> dict:
        return {}

    def get_request_file(self, file_name: str, file_binary: BinaryIO) -> dict:
        return {}

    def get_json_target_data_path(self) -> list[str]:
        return ["data", "content"]

    def get_json_target_data_pk_name(self) -> str:
        return "reviewId"

    def get_api_expected_success_status_codes(self) -> set[int]:
        return {200}

    def get_json_format(self) -> dict:
        return self._response_json_format

    def _get_nested_formant_json_attribute_mapping(self) -> dict:
        return {
            self.get_json_target_data_pk_name(): self._attribute_schema.REVIEW_ID,
            "reviewAt": self._attribute_schema.REVIEW_CREATED_DATETIME,
            "reviewTitle": self._attribute_schema.REVIEW_TITLE,
            "reviewContent": self._attribute_schema.REVIEW_CONTENTS,
            "rating": self._attribute_schema.REVIEW_STAR_RATING,
            "memberName": self._attribute_schema.REVIEW_WRITER_NAME,
            "attachment": {
                "imageAttachments": [
                    {
                        "imgSrc": self._attribute_schema.URL_IMAGE,
                    }
                ] * 10
            },
            "productId": self._attribute_schema.PRODUCT_OPTION_ID,
            "itemName": self._attribute_schema.ITEM_NAME,
            "vendorItemId": self._attribute_schema.PRODUCT_ID,
        }

    def get_max_retries(self) -> int:
        return self._max_retries

    def get_delay_seconds(self) -> float:
        return self._delay_seconds


# ===================================================
#  note
#
# - review scraping API 요청 시 start/end_time 설정 불가 (수집 날짜만 설정 가능)
# - review scraping API 요청 시 token 이 아닌 cookie 방식으로 요청
# - 검색 범위의 마지막 페이지가 넘어가면 content 에 빈 배열이 담겨 옴
# ===================================================
