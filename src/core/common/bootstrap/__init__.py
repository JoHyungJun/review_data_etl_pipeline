"""
__init__.py
-----------

애플리케이션 프로세스 실행에 요구되는 설정값, 클래스, 인스턴스 등 관련 전체 초기화 및 setup 모듈
"""


from core.common.bootstrap.config_schema_initialize import initialize_config_schema
from core.common.bootstrap.duckdb_initialize import initialize_duckdb
from core.common.bootstrap.logger_initialize import initialize_logger
from core.common.bootstrap.model.bootstrap_config import BootstrapConfig
from core.common.bootstrap.sentiment_model_initialize import initialize_sentiment_model


def run_bootstrap(config: BootstrapConfig) -> None:
    initialize_logger(
        root_log_path=config.application_log_path,
        sentiment_event_log_path=config.sentiment_event_log_path,
        sentiment_config_tuner_statistics_meta_log_path=config.sentiment_config_tuner_statistics_meta_log_path,
    )
    initialize_config_schema(
        schema_yaml_path=config.schema_yaml_path,
        schema_constants_py_path=config.schema_constants_py_path,
    )
    initialize_duckdb()
    initialize_sentiment_model(
        sentiment_model_path=config.sentiment_model_path
    )
