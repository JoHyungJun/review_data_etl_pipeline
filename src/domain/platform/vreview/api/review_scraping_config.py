"""
review_scraping_config.py
-------------------------

VReview 플랫폼 리뷰 스크래핑 설정 모듈

- 스크래핑 API 관련 정보 및 수집 데이터 포맷, save 경로 등의 설정값 제공
- BaseScrapConfig 를 상속받아 공통 스크래핑 API 설정 인터페이스 구현
"""


from pathlib import Path
from typing import Dict, List, Optional, Union, BinaryIO, Set, Literal

from core.base.domain.api.base_scraping_config import BaseScrapingConfig
from domain.platform.platform import Platform
from domain.platform.vreview.api.format.review_scraping_format import (
    VREVIEW_REVIEW_SCRAPING_RESPONSE_JSON_FORMAT
)
from domain.platform.vreview.schema.review_scraping_attribute_schema import VReviewReviewScrapingReviewAttributeSchema
from util.datetime_util import DAY_MILLISECONDS
from util.validate_util import (
    get_validated_and_parsed_unsigned_int,
    get_validated_date_by_str,
    get_validated_and_parsed_float, get_validated_and_parsed_optional_unsigned_int,
)


class VReviewReviewScrapingConfig(BaseScrapingConfig):
    """
    VReview 플랫폼 리뷰 스크래핑 설정 클래스

    - API 호출 정보 (API method, url, header, query params, body 등) 관리
    - 수집 시작/종료 날짜, 시간, 페이징 (per_page), token, 그룹/상품 id 설정
    - 스크래핑 시 재시도 횟수 (max_retries) 와 요청 간 딜레이 (delay_seconds) 설정
    - 플랫폼에서 제한한 최대 스크래핑 기한 (get_scrap_term_limit_ms) 설정
    """

    def __init__(
            self,
            shopping_mall_id: int,
            token: str,
            per_page: int,
            start_date: str,
            end_date: str,
            product_id: Optional[int],
            review_group_id: Optional[int],
            output_directory_path: Optional[Union[str, Path]] = None,
            max_retries: int = 3,
            delay_seconds: float = 1.0,
    ):
        self._shopping_mall_id = get_validated_and_parsed_unsigned_int(shopping_mall_id)
        self._token = token
        self._per_page = get_validated_and_parsed_unsigned_int(per_page)
        self._start_date = get_validated_date_by_str(start_date)
        self._end_date = get_validated_date_by_str(end_date)
        self._output_directory_path = Path(output_directory_path) if output_directory_path else None
        self._max_retries = get_validated_and_parsed_unsigned_int(max_retries)
        self._delay_seconds = get_validated_and_parsed_float(delay_seconds)

        self._review_group_id = get_validated_and_parsed_optional_unsigned_int(review_group_id)
        self._product_id = get_validated_and_parsed_optional_unsigned_int(product_id)

        if isinstance(review_group_id, int) and isinstance(product_id, int):
            raise ValueError("'상품 id' 와 '그룹 id' 는 모두 설정하지 않거나 둘 중 하나만 설정할 수 있습니다. 파라미터를 확인해주세요.")

        self._platform = Platform.VREVIEW
        self._attribute_schema = VReviewReviewScrapingReviewAttributeSchema
        self._response_json_format = VREVIEW_REVIEW_SCRAPING_RESPONSE_JSON_FORMAT

    def get_platform_kor_name(self) -> str:
        return self._platform.get_platform_kor_name()

    def get_platform_eng_name(self) -> str:
        return self._platform.get_platform_eng_name()

    def get_method(self) -> str:
        return "GET"

    def get_base_url(self) -> str:
        return f"https://one.vreview.tv/api/bidmin/v2/{self._shopping_mall_id}/reviews"

    def get_headers(self) -> dict:
        return {
            "Authorization": self._token,
            "Accept": "application/json",
            "Referer": "https://admin.vreview.tv/",
            "Origin": "https://admin.vreview.tv",
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
        return 365 * DAY_MILLISECONDS

    def get_query_params(
            self,
            page: int,
            start_date: Optional[str] = None,
            start_time: Optional[str] = None,
            end_date: Optional[str] = None,
            end_time: Optional[str] = None,
            review_group_id: Optional[Union[int, Literal[False]]] = None,
            product_id: Optional[Union[int, Literal[False]]] = None,
    ) -> Dict:
        """
        API request 용 query parameters 반환

        review_group_id, product_id 의 경우 둘 중 하나만 설정 가능하므로 분기 처리로 개별 설정
        - None/파라미터 명시 없음: 인스턴스 생성 시 초기화 된 값 사용
        - True: 인스턴스 생성 시 초기화 된 값 사용 (None 과 동일)
        - False: 해당 query parameter 삭제
        - int: 해당 값을 이용한 새로운 query parameter 반환 (인스턴스 내부 값 덮어쓰기)

        :param page: API 요청 페이지 번호
        :param start_date: API 요청 시작 날짜
        :param start_time: API 요청 시작 시간
        :param end_date: API 요청 끝 날짜
        :param end_time: API 요청 끝 시간
        :param review_group_id: API 요청 상품 그룹 id (Optional)
        :param product_id: API 요청 상품 id (Optional)
        :return: API 요청용 전체 query parameter dict
        """

        params = {
            "created_at_after": start_date or self._start_date,
            "created_at_before": end_date or self._end_date,
            "offset": page * self._per_page,
            "limit": self._per_page,
        }

        # Literal[False] 를 bool 로 혼동하여 True 값이 들어올 수도 있으므로, True 에 대한 분기도 처리 (not False)
        if review_group_id is not False:
            params["review_group_id"] = (
                get_validated_and_parsed_unsigned_int(review_group_id)
                if isinstance(review_group_id, int)
                else self._review_group_id
            )

        # Literal[False] 를 bool 로 혼동하여 True 값이 들어올 수도 있으므로, True 에 대한 분기도 처리 (not False)
        if product_id is not False:
            params["product_id"] = (
                get_validated_and_parsed_unsigned_int(product_id)
                if isinstance(product_id, int)
                else self._product_id
            )

        if params["review_group_id"] and params["product_id"]:
            raise ValueError("'상품 id' 와 '그룹 id' 는 모두 설정하지 않거나, 둘 중 하나만 설정할 수 있습니다. 파라미터를 확인해주세요.")

        return params

    def get_request_payload(self) -> Dict:
        return {}

    def get_request_file(self, file_name: str, file_binary: BinaryIO) -> Dict:
        return {}

    def get_json_target_data_path(self) -> List[str]:
        return ["results"]

    def get_json_target_data_pk_name(self) -> str:
        return "id"

    def get_api_expected_success_status_codes(self) -> Set[int]:
        return {200}

    def get_json_format(self) -> Dict:
        return self._response_json_format

    def _get_nested_formant_json_attribute_mapping(self) -> Dict:
        return {
            self.get_json_target_data_pk_name(): self._attribute_schema.REVIEW_ID,
            "author_name": self._attribute_schema.REVIEW_WRITER_NAME,
            "text": self._attribute_schema.REVIEW_CONTENTS,
            "is_visible": self._attribute_schema.IS_VISIBLE,
            "created_at": self._attribute_schema.REVIEW_CREATED_DATETIME,
            "product": {
                "id": self._attribute_schema.PRODUCT_ID,
                "remote_id": self._attribute_schema.PRODUCT_REMOTE_ID,
                "name": self._attribute_schema.PRODUCT_NAME,
            },
            "review_group": {
                "id": self._attribute_schema.REVIEW_GROUP_ID,
                "name": self._attribute_schema.REVIEW_GROUP_NAME,
            },
            "questions": [
                {
                    "question": self._attribute_schema.QUESTION,
                    "answer": self._attribute_schema.ANSWER,
                }
            ] * 10,
        }

    def get_max_retries(self) -> int:
        return self._max_retries

    def get_delay_seconds(self) -> float:
        return self._delay_seconds


# ===================================================
#  note
#
# - review scraping API 테스트 결과 PER_PAGE 가 10000 이상일 시 gateway error (5000까지 테스트 결과 ok)
# - review scraping API 요청 시 start/end_time 설정 불가 (수집 날짜만 설정 가능)
# ===================================================
