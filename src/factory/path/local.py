"""
local.py
--------

로컬 환경용 path 관련 빌더 모듈
"""


from pathlib import Path

from config.constant.path_constants import DATAS_DIRECTORY_PATH
from core.config.constant.schema_constants import COMMON
from core.config.model.config_registry import ConfigRegistry


def build_local_shopping_mall_platform_data_directory_path(
        config_registry: ConfigRegistry,
        platform_name: str,
) -> Path:
    """
    로컬 환경용 요청 회사별 데이터 디렉토리 경로 path 관련 빌더 메서드

    :param config_registry: 설정값이 담긴 인스턴스 ConfigRegistry
    :param platform_name: 대상 플랫폼명 str
    :return: 로컬 환경용 요청 회사별 데이터 디렉토리 경로 Path
    """

    return Path(
        DATAS_DIRECTORY_PATH
        / config_registry.get_value(
            section_key=COMMON.SECTION_KEY,
            option_name=COMMON.SHOPPING_MALL_NAME,
        )
        / platform_name
    )
