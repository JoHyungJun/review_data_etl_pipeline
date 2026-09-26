"""
file_uploader_builder.py
------------------------

로컬 환경용 파일 업로드 API 관련 config 인스턴스의 빌더 모듈
"""


from core.config.constant.schema_constants import VREVIEW
from core.config.model.config_registry import ConfigRegistry
from domain.platform.vreview.api.file_uploading_config import VreviewFileUploadingConfig


def build_vreview_file_uploading_config(config_registry: ConfigRegistry) -> VreviewFileUploadingConfig:
    """
    VReview 의 파일 업로드 API 관련 config 인스턴스인 VreviewFileUploadingConfig 를 반환

    :param config_registry: 설정값이 담긴 인스턴스
    :return: VreviewFileUploadingConfig 인스턴스
    """

    return VreviewFileUploadingConfig(
        shopping_mall_id=config_registry.get_value(
            section_key=VREVIEW.SECTION_KEY,
            option_name=VREVIEW.SHOPPING_MALL_ID,
        ),
        token=config_registry.get_value(
            section_key=VREVIEW.SECTION_KEY,
            option_name=VREVIEW.TOKEN,
        ),
    )
