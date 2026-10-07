"""
deploy.py
---------

배포 환경용 path 관련 빌더 모듈
"""


from pathlib import Path
from typing import Union

from core.config.constant.schema_constants import COMMON
from core.config.model.config_registry import ConfigRegistry


def build_deploy_shopping_mall_platform_data_directory_path(
        root_path: Union[Path, str],
        config_registry: ConfigRegistry,
        platform_name: str,
) -> str:
    """
    배포 환경용 요청 회사별 데이터 디렉토리 경로 path 관련 빌더 메서드

    주의 사항
    - 환경별 차이를 줄이기 위해 posix 를 이용한 str path 반환

    :param root_path: 배포 환경 저장소 root 경로 Union[Path, str]
    :param config_registry: 설정값이 담긴 인스턴스 ConfigRegistry
    :param platform_name: 대상 플랫폼명 str
    :return: 배포 환경용 요청 회사별 데이터 디렉토리 경로 str
    """

    return Path(
        root_path
        / config_registry.get_value(
            section_key=COMMON.SECTION_KEY,
            option_name=COMMON.SHOPPING_MALL_NAME,
        )
        / platform_name
    ).as_posix()
