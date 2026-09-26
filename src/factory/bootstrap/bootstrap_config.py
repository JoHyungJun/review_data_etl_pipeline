"""
bootstrap_config.py
-------------------

로컬 전용 애플리케이션 bootstrap 과정에서 필요한 설정값 정보 관리 상수 클래스 모듈
"""


from config.constant.path_constants import TRAINED_SENTIMENT_MODEL_DIRECTORY_PATH, CONFIG_SCHEMA_YML_PATH, \
    SCHEMA_CONSTANTS_PY_PATH
from core.common.bootstrap.model.bootstrap_config import BootstrapConfig


LOCAL_BOOTSTRAP_CONFIG = BootstrapConfig(
    schema_yaml_path=CONFIG_SCHEMA_YML_PATH,
    schema_constants_py_path=SCHEMA_CONSTANTS_PY_PATH,

    sentiment_model_path=TRAINED_SENTIMENT_MODEL_DIRECTORY_PATH,
)