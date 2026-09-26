"""
config_schema_initialize.py
---------------------------

애플리케이션 프로세스 실행에 요구되는 설정값 스키마 관련 관련 초기화 및 setup 모듈
"""


from pathlib import Path
from typing import Union

from core.config.util.config_codegen import generate_constants_from_schema
from core.config.util.config_util import setup_yaml, initialize_singleton_schema, get_singleton_schema
from util.logging_util import logging_error_event


def initialize_config_schema(
        schema_yaml_path: Union[Path, str],
        schema_constants_py_path: Union[Path, str],
) -> None:
    """
    애플리케이션 프로세스 실행에 요구되는 설정값 스키마 관련
    초기화 및 setup 수행

    주요 역할
    - 스키마 load 및 싱글톤 인스턴스 초기화
    - 스키마 정보를 yaml 파일에 반영

    :param schema_yaml_path: 스키마 산출 후 YAML save 경로 Union[Path, str]
    :param schema_constants_py_path: 스키마 산출 후 상수 모듈 save 경로 Union[Path, str]
    :return: 없음
    """

    try:
        schema_yaml_path = Path(schema_yaml_path)
        schema_constants_py_path = Path(schema_constants_py_path)

        # 싱글톤 스키마 초기화
        initialize_singleton_schema()
        schema = get_singleton_schema()

        # 스키마 정보 yaml 반영
        setup_yaml(schema_yaml_path)

        # 스키마 정보 상수 반영
        generate_constants_from_schema(schema, schema_constants_py_path)

    except Exception as e:
        logging_error_event(
            exception_instance=e,
            log_message="While initializing config schema",
            log_message_detail=str(e),
            log_metadata={
                "process": "initialize_config_schema",
                "schema_yaml_path": schema_yaml_path,
                "schema_constants_py_path": schema_constants_py_path,
            },
        )
        raise
