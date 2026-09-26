"""
sentiment_config.py
-------------------

감성 추론 모델 관련 정적 설정 정보 관리 클래스 모듈

주의 사항
- 해당 객체는 immutable (read-only) 설정 객체
- 해당 객체의 초기화는 애플리케이션 최초 실행 setup 시 한 번만 실행을 권고
- runtime 중 설정 변경 및 mutation 금지
"""


from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

from config.constant.name_constants import SENTIMENT_CONFIG_JSON_FILE_NAME
from util.logging_util import logging_error_event
from util.validate_util import get_validated_between_zero_and_one_float, get_validated_over_one_float, \
    get_validated_and_parsed_unsigned_int


@dataclass(frozen=True)
class SentimentConfig:
    """
    감성 추론 모델 관련 정적 설정 정보 관리 클래스

    load() 시에 외부 설정 파일에 접근하여 내부 변수를 초기화 및 검증한 객체를 반환하며,
    일부 변수의 경우 설정 파일에 누락되어 있어도 default 값을 허용
    (도메인/데이터 및 환경/호스트 머신 별 추정치 관련 설정값은 default 값을 금지)

    주의 사항
    - 해당 클래스는 일반적인 객체 생성 방법 (SentimentConfig()) 으로 초기화 및 객체 생성을 권고하지 않으며,
      load() 를 활용해 외부 설정 파일의 값으로 초기화 및 검증된 객체를 반환 받고 사용하길 권고
    - 설정값 관련 파일은 반드시 지정된 경로에 위치해야 하며, path 는 해당 클래스가 관리하는 상수로 접근해야 함
    """

    CONFIG_FILE_PATH: ClassVar[Path] = Path(__file__).parent / SENTIMENT_CONFIG_JSON_FILE_NAME

    def __post_init__(self):
        # 개별 변수 data type validate
        object.__setattr__(
            self,
            "max_text_length",
            get_validated_and_parsed_unsigned_int(self.max_text_length),
        )
        object.__setattr__(
            self,
            "memory_usage_ratio",
            get_validated_between_zero_and_one_float(self.memory_usage_ratio),
        )
        object.__setattr__(
            self,
            "oom_token_reduction_ratio",
            get_validated_between_zero_and_one_float(self.oom_token_reduction_ratio),
        )
        object.__setattr__(
            self,
            "min_padding_efficiency_ratio",
            get_validated_between_zero_and_one_float(self.min_padding_efficiency_ratio),
        )
        object.__setattr__(
            self,
            "min_throughput_improvement_ratio",
            get_validated_over_one_float(self.min_throughput_improvement_ratio),
        )
        object.__setattr__(
            self,
            "measure_count",
            get_validated_and_parsed_unsigned_int(self.measure_count),
        )

    # required
    # 개별 리뷰 최대 허용 text length (P90 기반 권장)
    max_text_length: int

    # optional
    # 환경/호스트 머신/device 별 남은 메모리 중 얼마나 추론 연산에 활용할 것인가 에 대한 비율
    memory_usage_ratio: float = 0.7

    # OOM (Out-Of-Memory) 발생 시 fallback 과정에서 batch 별 최대 허용 토큰 개수를 감소 시킬 비율
    oom_token_reduction_ratio: float = 0.7

    # batch 에 담긴 개별 text 길이 차이가 얼마나 있을 때 batch 를 분리할 것인가 에 대한 비율
    min_padding_efficiency_ratio: float = 0.4

    # throughput 증가율 임계값
    min_throughput_improvement_ratio: float = 1.05

    # throughput 측정 반복 횟수
    measure_count: int = 3

    @classmethod
    def load(cls) -> SentimentConfig:
        config_file_path = cls.CONFIG_FILE_PATH

        try:
            with open(config_file_path, "r", encoding="utf-8") as f:
                config_dict = json.load(f)
        except Exception as e:
            logging_error_event(
                exception_instance=e,
                log_message="While reading sentiment config file",
                log_metadata={
                    "file_path": config_file_path
                },
            )
            raise

        # 정의된 필드만 필터링
        valid_fields = {f.name for f in dataclasses.fields(cls)}
        filtered_config = {k: v for k, v in config_dict.items() if k in valid_fields}

        # 외부 파일에 required 변수 누락 시 error
        try:
            return cls(**filtered_config)
        except TypeError as e:
            raise ValueError(
                f"감성 추론 관련 설정값을 구성하는 과정에서 필수 값이 누락되었습니다. "
                f"코드 혹은 {config_file_path} 파일을 확인해주세요 : {e}"
            ) from e

    @classmethod
    def get_storage_path(cls):
        return cls.CONFIG_FILE_PATH
