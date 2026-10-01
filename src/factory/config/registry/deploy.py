"""
deploy.py
---------

배포 환경용 ConfigRegistry 및 프로세스 초기화 관련 ConfigRegistry 인스턴스의 빌더 모듈
"""


from core.config.model.config_registry import ConfigRegistry
from entry.deploy.config.api.adapter.api_config_adapter import ApiConfigAdapter
from entry.deploy.config.api.dto.base.base_api_request import BaseApiRequest


def build_deploy_api_config_registry(request: BaseApiRequest) -> ConfigRegistry:
    """
    배포 환경용 API ConfigRegistry initializer

    배포/API 환경용 지정된 경로의 스키마 및 request API 요청 객체에서 데이터를 추출하고 ConfigRegistry 인스턴스 반환

    주의 사항
    - 해당 메서드 실행 이전 반드시 config schema 싱글톤 인스턴스가 초기화되어 있어야 함

    :param request: request 요청된 API 객체 BaseApiRequest
    :return: 배포용 경로에서 추출한 데이터로 초기화된 ConfigRegistry 인스턴스
    """

    parsed_api_data = ApiConfigAdapter.load_to_section_based_dict(request)

    return ConfigRegistry(section_based_config_dict=parsed_api_data)


