"""
review_hiding_config.py
-----------------------

VReview 플랫폼 리뷰 숨김 처리 설정 모듈

- 리뷰 숨김 API 관련 정보 등의 설정값 제공
- BaseApiConfig 를 상속받아 공통 API 설정 인터페이스 구현
"""


from typing import BinaryIO, Optional, List, Dict, Set

from core.base.domain.api.base_api_config import BaseApiConfig
from domain.platform.platform import Platform
from util.validate_util import get_validated_and_parsed_unsigned_int, get_validated_and_parsed_float


class VreviewReviewHidingConfig(BaseApiConfig):
    """
    VReview 플랫폼 Excel 리뷰 숨김 처리 설정 클래스

    - API 호출 정보 (API method, url, header, query params, body 등) 관리
    - JSON 포맷, 숨김 처리의 최대 리뷰 개수 (hide_batch_size) 관리
    - 파일 이관 시 재시도 횟수 (max_retries) 와 요청 간 딜레이 (delay_seconds) 설정
    """

    def __init__(
            self,
            shopping_mall_id: int,
            token: str,
            batch_size: int,
            max_retries: int = 3,
            delay_seconds: float = 1.0,
    ):
        self._shopping_mall_id = get_validated_and_parsed_unsigned_int(shopping_mall_id)
        self._token = token
        self._batch_size = get_validated_and_parsed_unsigned_int(batch_size)
        self._max_retries = get_validated_and_parsed_unsigned_int(max_retries)
        self._delay_seconds = get_validated_and_parsed_float(delay_seconds)

        self._platform = Platform.VREVIEW

    def get_platform_kor_name(self) -> str:
        return self._platform.get_platform_kor_name()

    def get_platform_eng_name(self) -> str:
        return self._platform.get_platform_eng_name()

    def get_method(self) -> str:
        return "PUT"

    def get_base_url(self) -> str:
        return f"https://one.vreview.tv/api/bidmin/v2/{self._shopping_mall_id}/reviews/hide"

    def get_headers(self) -> Dict:
        return {
            "Authorization": self._token,
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json"
        }

    def get_query_params(
            self,
            page: int,
            start_date: Optional[str] = None,
            start_time: Optional[str] = None,
            end_date: Optional[str] = None,
            end_time: Optional[str] = None
    ) -> Dict:
        return {}

    def get_request_payload(self, review_ids: List[int]) -> Dict:
        return {
            "reviews": review_ids,
        }

    def get_request_file(self, file_name: str, file_binary: BinaryIO) -> Dict:
        pass

    def get_api_expected_success_status_codes(self) -> Set[int]:
        return {200}

    def get_max_retries(self) -> int:
        return self._max_retries

    def get_delay_seconds(self) -> float:
        return self._delay_seconds

    # noinspection PyMethodMayBeStatic
    # 이 메서드는 통일성을 위해 BaseScrapingConfig 인터페이스의 메서드에서 차용
    def get_api_target_data_path(self) -> List[str]:
        return ["Reviews to be hidden"]

    def get_batch_size(self) -> int:
        return self._batch_size
