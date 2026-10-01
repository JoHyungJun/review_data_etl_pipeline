"""
deploy_application.py
---------------------

배포 애플리케이션 실행 관련 클래스 모듈

배포 환경 필수 세팅 검증 및 bootstrap 수행 후 요청된 프로세스 실행

주의 사항
- 현재 배포 환경의 Application 은 내부 규칙에 의해 단일 실행 방식이 선택 및 실행되며,
  이후 추가적인 기능 확장 시 현재 모듈이 그에 따른 분기의 책임을 담당하여 구현되어야 함
"""


from pathlib import Path

import uvicorn

from config.constant.common.name_constants import (
    SRC_DIRECTORY_NAME,
)
from config.constant.common.path_constants import BASE_DIRECTORY_PATH, CONFIG_SCHEMA_YML_PATH, SCHEMA_CONSTANTS_PY_PATH
from core.common.bootstrap import run_bootstrap
from core.common.bootstrap.model.bootstrap_config import BootstrapConfig
from entry.deploy.config.api.application import application
from util.runtime_environment_util import resolve_value_from_environment_variables


class DeployApplication:

    SENTIMENT_MODEL_PATH_ENVIRONMENT_KEY = "SENTIMENT_MODEL_PATH"

    APPLICATION_LOG_PATH_ENVIRONMENT_KEY = "APPLICATION_LOG_PATH"
    SENTIMENT_EVENT_LOG_PATH_ENVIRONMENT_KEY = "SENTIMENT_EVENT_LOG_PATH"
    SENTIMENT_CONFIG_TUNER_STATISTICS_META_LOG_PATH_ENVIRONMENT_KEY = "SENTIMENT_CONFIG_TUNER_STATISTICS_META_LOG_PATH"

    def __init__(self):
        # bootstrap 을 위한 데이터 path 정보를 환경변수에서 추출
        sentiment_model_path = resolve_value_from_environment_variables(
            self.SENTIMENT_MODEL_PATH_ENVIRONMENT_KEY
        )
        application_log_path = resolve_value_from_environment_variables(
            self.APPLICATION_LOG_PATH_ENVIRONMENT_KEY
        )
        sentiment_event_log_path = resolve_value_from_environment_variables(
            self.SENTIMENT_EVENT_LOG_PATH_ENVIRONMENT_KEY
        )
        sentiment_config_tuner_statistics_meta_log_path = resolve_value_from_environment_variables(
            self.SENTIMENT_CONFIG_TUNER_STATISTICS_META_LOG_PATH_ENVIRONMENT_KEY
        )

        # Path 로 파싱
        sentiment_model_path = Path(sentiment_model_path)
        application_log_path = Path(application_log_path)
        sentiment_event_log_path = Path(sentiment_event_log_path)
        sentiment_config_tuner_statistics_meta_log_path = Path(sentiment_config_tuner_statistics_meta_log_path)

        self.bootstrap_config = BootstrapConfig(
            schema_yaml_path=CONFIG_SCHEMA_YML_PATH,
            schema_constants_py_path=SCHEMA_CONSTANTS_PY_PATH,

            sentiment_model_path=sentiment_model_path,

            application_log_path=application_log_path,
            sentiment_event_log_path=sentiment_event_log_path,
            sentiment_config_tuner_statistics_meta_log_path=sentiment_config_tuner_statistics_meta_log_path,
        )

    @staticmethod
    def _validate_environment() -> None:
        """
        배포 환경 구동에 필수적인 사항 검증 내부용 메서드

        동작 방식
        - 프로젝트 구조 검증
        - TODO: 외부 연결 등 검사

        :return: 없음
        """

        root_directory = BASE_DIRECTORY_PATH
        deploy_required_directories = {
            SRC_DIRECTORY_NAME,
        }

        missing_directories = {
            directory_name
            for directory_name in deploy_required_directories
            if not (root_directory / directory_name).is_dir()
        }

        if missing_directories:
            missing_directory_names = ", ".join(
                sorted(missing_directories)
            )

            raise RuntimeError(
                f"배포 환경에 필요한 디렉토리가 존재하지 않습니다. : "
                f"{missing_directory_names}"
            )

    def run(self) -> None:
        """
        배포 환경 실행 진입 메서드

        동작 방식
        - 배포 환경 관련 필수부 검증
        - 배포 환경 관련 bootstrap 수행
        - FastAPI 실행

        :return: 없음
        """

        # validate
        self._validate_environment()

        # bootstrap
        run_bootstrap(self.bootstrap_config)

        # run
        uvicorn.run(
            app=application,
            host="0.0.0.0",
            port=8000,
        )
