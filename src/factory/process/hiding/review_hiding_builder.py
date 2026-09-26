"""
review_hiding_builder.py
------------------------

로컬 환경용 리뷰 숨기기 API 관련 config 인스턴스의 빌더 모듈
"""


from core.config.constant.schema_constants import VREVIEW
from core.config.model.config_registry import ConfigRegistry
from domain.platform.vreview.api.review_hiding_config import VreviewReviewHidingConfig


def build_vreview_review_hiding_config(config_registry: ConfigRegistry) -> VreviewReviewHidingConfig:
    """
    VReview 의 리뷰 숨기기 API 관련 config 인스턴스인 VreviewReviewHidingConfig 를 반환

    :param config_registry: 설정값이 담긴 인스턴스 ConfigRegistry
    :return: VreviewReviewHideConfig 인스턴스 VreviewReviewHidingConfig
    """

    return VreviewReviewHidingConfig(
        token=config_registry.get_value(
            section_key=VREVIEW.SECTION_KEY,
            option_name=VREVIEW.TOKEN,
        ),
        batch_size=config_registry.get_value(
            section_key=VREVIEW.SECTION_KEY,
            option_name=VREVIEW.HIDE_BATCH_SIZE,
        ),
    )
