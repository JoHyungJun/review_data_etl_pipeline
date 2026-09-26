"""
local_application.py
--------------------

로컬 애플리케이션 실행 관련 클래스 모듈

외부 설정값 기반, 로컬 환경 필수 세팅 검증 및 bootstrap 수행 후 플랫폼별 파이프라인을 조립하고 실행

주의 사항
- 현재 로컬 환경의 Application 은 내부 규칙에 의해 단일 실행 방식이 선택 및 실행되며,
  이후 추가적인 기능 확장 시 현재 모듈이 그에 따른 분기의 책임을 가지고,
  현재 모듈이 호출하는 외부 메서드가 전략에 따라 파이프라인 객체를 조립하여 전달
"""


import logging

from config.constant.common.name_constants import (
    SRC_DIRECTORY_NAME,
    DATAS_DIRECTORY_NAME,
    SENTIMENT_MODEL_DIRECTORY_NAME,
    CONFIG_DIRECTORY_NAME,
    LOGS_DIRECTORY_NAME,
)
from config.constant.common.path_constants import BASE_DIRECTORY_PATH
from core.base.pipeline.base_process_pipeline import BaseProcessPipeline
from core.common.bootstrap import run_bootstrap
from core.config.constant.schema_constants import COMMON
from domain.export.export import Export
from entry.orchestration.export_pipeline_applier import export_pipeline_applier
from error.config import ConfigNotAvailableError
from factory.bootstrap.config.local import LOCAL_BOOTSTRAP_CONFIG
from factory.config.registry.local import build_local_config_registry
from util.logging_util import logging_error_event


class LocalApplication:

    def __init__(self):
        self.bootstrap_config = LOCAL_BOOTSTRAP_CONFIG

    @staticmethod
    def _validate_environment() -> None:
        """
        로컬 환경 구동에 필수적인 사항 검증 내부용 메서드

        동작 방식
        - 프로젝트 구조 검증

        :return: 없음
        """

        root_directory = BASE_DIRECTORY_PATH
        local_required_directories = {
            SRC_DIRECTORY_NAME,
            DATAS_DIRECTORY_NAME,
            SENTIMENT_MODEL_DIRECTORY_NAME,
            CONFIG_DIRECTORY_NAME,
            LOGS_DIRECTORY_NAME,
        }

        missing_directories = {
            directory_name
            for directory_name in local_required_directories
            if not (root_directory / directory_name).is_dir()
        }

        if missing_directories:
            missing_directory_names = ", ".join(
                sorted(missing_directories)
            )

            raise RuntimeError(
                f"로컬 환경에 필요한 디렉토리가 존재하지 않습니다. : "
                f"{missing_directory_names}"
            )

    def run(self) -> None:
        """
        로컬 환경 실행 진입 메서드

        동작 방식
        - 로컬 환경 관련 필수부 검증
        - 로컬 환경 관련 bootstrap 수행
        - 파이프라인 조립 및 실행

        :return: 없음
        """

        # validate
        self._validate_environment()

        # bootstrap
        run_bootstrap(self.bootstrap_config)
        config_registry = build_local_config_registry()

        # run
        export_id = config_registry.get_value(
            section_key=COMMON.SECTION_KEY,
            option_name=COMMON.EXPORT_ID,
        )

        pipelines: list[BaseProcessPipeline] = export_pipeline_applier(
            export=Export.from_id(export_id),
            config_registry=config_registry,
        )

        for pipeline in pipelines:
            try:
                pipeline.run_pipeline()

            except ConfigNotAvailableError as e:
                logging.warning(
                    f"[SKIP] platform={pipeline.get_platform().get_platform_eng_name()}: "
                    f"Some values are not defined in config registry - {str(e)}"
                )
                continue

            except Exception as e:
                logging_error_event(
                    exception_instance=e,
                    log_metadata={
                        "platform": pipeline.get_platform().get_platform_eng_name(),
                    },
                    log_message="While running local application",
                    log_message_detail=str(e),
                )
                continue
