"""
local.py
--------

로컬 전용 애플리케이션 bootstrap 과정에서 필요한 설정값 정보 관리 상수 클래스 모듈
"""


from config.constant.common.path_constants import (
    CONFIG_SCHEMA_YML_PATH,
    SCHEMA_CONSTANTS_PY_PATH,
)
from config.constant.local.path_constants import (
    LOCAL_TRAINED_SENTIMENT_MODEL_DIRECTORY_PATH,
    LOCAL_SENTIMENT_CONFIG_TUNER_STATISTICS_META_LOG_JSONL_PATH,
    LOCAL_SENTIMENT_EVENT_LOG_JSONL_PATH,
    LOCAL_APPLICATION_LOG_PATH,
)
from core.common.bootstrap.model.bootstrap_config import BootstrapConfig


LOCAL_BOOTSTRAP_CONFIG = BootstrapConfig(
    schema_yaml_path=CONFIG_SCHEMA_YML_PATH,
    schema_constants_py_path=SCHEMA_CONSTANTS_PY_PATH,

    sentiment_model_path=LOCAL_TRAINED_SENTIMENT_MODEL_DIRECTORY_PATH,

    application_log_path=LOCAL_APPLICATION_LOG_PATH,
    sentiment_event_log_path=LOCAL_SENTIMENT_EVENT_LOG_JSONL_PATH,
    sentiment_config_tuner_statistics_meta_log_path=LOCAL_SENTIMENT_CONFIG_TUNER_STATISTICS_META_LOG_JSONL_PATH,
)
