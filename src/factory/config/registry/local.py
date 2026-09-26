"""
local.py
--------

로컬 환경용 ConfigRegistry 및 프로세스 초기화 관련 ConfigRegistry 인스턴스의 빌더 모듈
"""

from config.constant.local.path_constants import LOCAL_CONFIG_INI_PATH
from core.config.model.config_registry import ConfigRegistry
from core.config.adapter.ini_config_adapter import IniConfigAdapter


def build_local_config_registry() -> ConfigRegistry:
    """
    로컬 환경용 ConfigRegistry initializer

    로컬용으로 지정된 경로의 스키마 및 설정 파일에서 데이터를 추출하고 ConfigRegistry 인스턴스 반환

    주의 사항
    - 해당 메서드 실행 이전 반드시 config schema 싱글톤 인스턴스가 초기화되어 있어야 함

    :return: 로컬용 경로에서 추출한 데이터로 초기화된 ConfigRegistry 인스턴스
    """

    parsed_ini_data = IniConfigAdapter.load_to_section_based_dict(LOCAL_CONFIG_INI_PATH)

    return ConfigRegistry(section_based_config_dict=parsed_ini_data)


