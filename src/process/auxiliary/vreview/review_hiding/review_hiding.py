"""
review_hiding.py
----------------

VReview 에 등록된 리뷰 숨김 처리 모듈
VReview 는 등록된 리뷰가 삭제되지 않고 숨김 처리되며,
중복 요청에 대해 멱등성을 보장하며 허용하나 성공 여부 response 에는 담겨 오지 않음

주요 메서드
- review_hiding: 전체 프로세스 실행 중심부
"""


import logging
from typing import Optional

from domain.platform.platform import Platform
from domain.platform.vreview.api.review_hiding_config import VreviewReviewHidingConfig
from util.api_util import get_expected_status_response_safely_with_retries
from util.json_util import extract_target_data
from util.logging_util import run_with_logging


@run_with_logging(
    lambda *args, **kwargs: (
        {"platform": kwargs["platform"].get_platform_eng_name()}
        if kwargs.get("platform") is not None
        else {}
    )
)
def review_hiding(
        platform: Optional[Platform],
        hiding_config: VreviewReviewHidingConfig,
        target_review_ids: list[int],
) -> None:
    """
    VReview 에 등록된 리뷰 숨김 처리 관련 중심부

    :param platform: 숨김 대상 데이터의 플랫폼 정보 Optional[Platform]
                     (로그 처리를 위한 인자이며, 반드시 keyword argument 방식으로 인자를 넘겨야 함)
    :param hiding_config: VReview 리뷰 숨김 관련 설정값을 가진 인스턴스
    :param target_review_ids: 숨김 대상 리뷰 id list[int]
    :return: 없음
    """

    # 중복 id 제거
    target_review_ids = list(dict.fromkeys(target_review_ids))

    # batch 만큼씩 API 안전 요청
    batch_size = hiding_config.get_batch_size()
    for i in range(0, len(target_review_ids), batch_size):
        batch = target_review_ids[i: i + batch_size]
        request_ids_count = len(set(batch))
        logging.info(f"[START] target_count={request_ids_count}: Review hiding")

        # API request
        response = get_expected_status_response_safely_with_retries(
            method=hiding_config.get_method(),
            base_url=hiding_config.get_base_url(),
            headers=hiding_config.get_headers(),
            payload=hiding_config.get_request_payload(review_ids=batch),
            expected_status_codes=hiding_config.get_api_expected_success_status_codes(),
        )

        # response 검증
        json_data = response.json()
        hidden_review_ids = extract_target_data(
            data=json_data,
            json_target_data_path=hiding_config.get_api_target_data_path(),
        )

        # 정상 요청이었다면 요청된 모든 id 가 숨김 처리 후 response 에 담겨야 하지만,
        # 이전에 숨김 처리돼 있었던 리뷰의 경우 별다른 에러 없이 response 에만 담기지 않기 때문에 warn 로그 처리
        response_ids_count = len(set(hidden_review_ids))
        if request_ids_count != response_ids_count:
            logging.warning(f"[FAILED] request_target_count={request_ids_count}, "
                            f"response_target_count={response_ids_count}: "
                            f"Not all requested reviews were hidden: Some reviews were already hidden")

        logging.info(f"[END] response_target_count={response_ids_count}: Review hiding")
