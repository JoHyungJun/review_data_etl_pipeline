"""
sentiment_model.py
------------------

감성 추론 모델 singleton 관리 클래스 모듈

주요 역할
- transformers 기반 sentiment model / tokenizer load
- 애플리케이션 생명 주기 동안 단일 모델 인스턴스 재사용
- 추론 모델 및 환경/호스트 관련 runtime 정보 관리

주의 사항
- 해당 객체의 초기화 (initialize_sentiment_model()) 는 애플리케이션 최초 실행 setup 시 한 번만 실행을 권고
  (많은 리소스와 오버헤드를 유발함)
"""


from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Optional, Union

import torch
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    PreTrainedModel,
    PreTrainedTokenizer,
)

from process.core.postprocess.postprocessing.postprocessor.common.sentiment.util.token_batch_util \
    import calculate_optimal_token_count_per_batch
from process.core.postprocess.postprocessing.postprocessor.common.sentiment.config.sentiment_config \
    import SentimentConfig
from util.runtime_environment_util import (
    get_available_inference_device,
    estimate_max_token_count_per_batch,
)


class SentimentModel:
    """
    감성 추론 모델 singleton 관리 클래스

    감성 추론에 활용되는 PreTrainedModel, PreTrainedTokenizer 객체 및
    환경, 호스트 별 최적의 batch size 를 계산 후 관리

    해당 객체는 static 한 성격으로 별도의 객체 생성 없이 class method 로 활용할 수 있지만,
    관리하는 변수들의 초기화를 위해 반드시 한 번의 initialize_sentiment_model() 호출이 요구됨
    """

    _lock = threading.Lock()

    _config: Optional[SentimentConfig] = None

    _device: Optional[torch.device] = None

    _model: Optional[PreTrainedModel] = None
    _tokenizer: Optional[PreTrainedTokenizer] = None

    _optimal_token_count_per_batch: Optional[int] = None

    _is_initialized = False

    @classmethod
    def initialize_sentiment_model(
            cls,
            model_path: Union[str, Path],
            sentiment_config: SentimentConfig,
    ) -> None:
        """
        생성자를 대체하는, 내부 변수를 초기화하는 메서드

        해당 클래스는 @classmethod 를 통해 static 하게 사용되기 때문에,
        애플리케이션의 실행 시점 setup 단계에서 해당 메서드를 호출하여 초기화해야 함

        :param model_path: 감성 추론 모델이 위치하는 디렉토리 경로 Union[str, Path]
        :param sentiment_config: 감성 추론 모델 설정값 관리 클래스 SentimentConfig
        :return: 없음
        """

        if cls._is_initialized:
            return

        # 동시 initialized 방어
        with cls._lock:
            if cls._is_initialized:
                return

            cls._config = sentiment_config

            cls._model = AutoModelForSequenceClassification.from_pretrained(model_path)
            cls._tokenizer = AutoTokenizer.from_pretrained(model_path)

            # 현재 호스트 머신이 지원하는 CPU/GPU 정보 추출 및 model 에 해당 자원 부여
            cls._device = get_available_inference_device()
            cls._model.to(cls._device)
            cls._model.eval()

            # 최적의 토큰 개수 측정 및 할당
            cls._optimal_token_count_per_batch = calculate_optimal_token_count_per_batch(
                model=cls._model,
                tokenizer=cls._tokenizer,
                max_token_count_per_batch=estimate_max_token_count_per_batch(
                    model=cls._model,
                    device=cls._device,
                    memory_usage_ratio=cls._config.memory_usage_ratio,
                ),
                max_text_length=cls._config.max_text_length,
                measure_count=cls._config.measure_count,
                min_throughput_improvement_ratio=cls._config.min_throughput_improvement_ratio,
            )

            logging.info(
                f"[LOAD] sentiment_model={cls._model.__class__.__name__}, "
                f"tokenizer={cls._tokenizer.__class__.__name__}, "
                f"device={cls._device}, "
                f"optimal_token_count_per_batch={cls._optimal_token_count_per_batch}, "
                f"model_path={model_path}"
            )

            cls._is_initialized = True

    @classmethod
    def _check_initialized(cls) -> None:
        if not cls._is_initialized:
            raise ValueError(
                "아직 모델 및 설정 관련 클래스가 초기화되지 않았습니다. 코드를 확인해주세요."
            )

    @classmethod
    def get_model_and_tokenizer(cls) -> tuple[PreTrainedModel, PreTrainedTokenizer]:
        cls._check_initialized()

        if cls._model is None or cls._tokenizer is None:
            raise ValueError(
                "감성 추론 모델 (PreTrainedModel, PreTrainedTokenizer) 이 load 되지 못했습니다. "
                "관련 디렉토리 혹은 코드를 확인해주세요."
            )

        return cls._model, cls._tokenizer

    @classmethod
    def get_optimal_token_count_per_batch(cls) -> int:
        cls._check_initialized()

        if cls._optimal_token_count_per_batch is None:
            raise ValueError(
                "클래스의 초기화 과정 혹은 알 수 없는 이유로 인해 해당 변수가 초기화되지 못했습니다. "
                "코드 혹은 로그를 확인해주세요. : _optimal_token_count_per_batch"
            )

        return cls._optimal_token_count_per_batch

    @classmethod
    def get_device(cls) -> torch.device:
        cls._check_initialized()

        if cls._device is None:
            raise ValueError(
                "클래스의 초기화 과정 혹은 알 수 없는 이유로 인해 해당 변수가 초기화되지 못했습니다. "
                "코드 혹은 로그를 확인해주세요. : _device"
            )

        return cls._device

    @classmethod
    def get_config(cls) -> SentimentConfig:
        cls._check_initialized()

        if cls._config is None:
            raise ValueError(
                "클래스의 초기화 과정 혹은 알 수 없는 이유로 인해 해당 변수가 초기화되지 못했습니다. "
                "코드 혹은 로그를 확인해주세요. : _config"
            )

        return cls._config

    @classmethod
    def update_config(cls, updated_config: SentimentConfig) -> None:
        """
        해당 클래스 싱글톤 객체에서 관리하고 있던 SentimentConfig 를 교체 후 후속 처리

        무거운 연산을 수행하여, 애플리케이션 실행 시점에만 호출이 권고되는 initialize_sentiment_model() 메서드와 다르게,
        해당 메서드는 간소한 후속 연산으로, 애플리케이션 실행 중 config 교체가 필요한 경우 호출 권고

        config 가 관리하는 변수 값에 의존하는 해당 클래스 내부 변수들을 재계산

        :param updated_config:
        :return:
        """

        cls._check_initialized()

        with cls._lock:
            if cls._config is None:
                raise ValueError(
                    "클래스의 초기화 과정 혹은 알 수 없는 이유로 인해 해당 변수가 초기화되지 못했습니다. "
                    "코드 혹은 로그를 확인해주세요. : _config"
                )

            previous_config = cls._config

            if (
                    previous_config.max_text_length != updated_config.max_text_length
                    or previous_config.memory_usage_ratio != updated_config.memory_usage_ratio
            ):
                previous_optimal_token_count_per_batch = cls._optimal_token_count_per_batch

                cls._optimal_token_count_per_batch = estimate_max_token_count_per_batch(
                    model=cls._model,
                    device=cls._device,
                    memory_usage_ratio=updated_config.memory_usage_ratio,
                )

                logging.info(
                    f"[UPDATE] previous_optimal_token_count_per_batch={previous_optimal_token_count_per_batch}, "
                    f"updated_optimal_token_count_per_batch={cls._optimal_token_count_per_batch}: "
                    f"Update sentiment model while updating sentiment config"
                )

            cls._config = updated_config

            logging.info(
                f"[UPDATE] previous_config={previous_config}, updated_config={cls._config}: "
                f"Update sentiment config in singleton sentiment model"
            )
