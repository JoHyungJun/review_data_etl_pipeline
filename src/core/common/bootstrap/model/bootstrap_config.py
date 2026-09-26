"""
bootstrap_config.py
-------------------

애플리케이션 bootstrap 과정에서 필요한 설정값 정보 관리 클래스 모듈
"""


from dataclasses import dataclass
from pathlib import Path
from typing import Union


@dataclass(frozen=True)
class BootstrapConfig:
    
    # 설정값 스키마 관련
    schema_yaml_path: Union[Path, str]
    schema_constants_py_path: Union[Path, str]
    
    # 감성 추론 관련
    sentiment_model_path: Union[Path, str]