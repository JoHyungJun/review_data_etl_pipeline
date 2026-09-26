"""
models.py
---------

감성 추론 로깅에서 사용되는 이벤트 성격 단위 데이터 객체 모듈

BaseSentimentLog 부모 클래스로 공통 포맷을 따르게 하되,
해당 클래스를 상속하는 자식 클래스는 반드시 개별 event 를 선언 시 초기화해야 하며,
이 정보는 로그 데이터로부터의 역직렬화에 활용됨

해당 데이터 객체들은 로그 작성 시에 활용될 것이므로,
직렬화/역직렬화 에러를 방어하기 위해 BaseSentimentLog 내부의 직렬화/역직렬화용 메서드 활용 권고
"""


from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import ClassVar, Type, get_type_hints, Any

import torch

from process.core.postprocess.postprocessing.postprocessor.common.sentiment.log.util.serializer import serialize_log_value, \
    deserialize_log_value
from process.core.postprocess.postprocessing.postprocessor.common.sentiment.model.batch_snapshot import BatchSnapshot, \
    BatchSnapshotSummary
from process.core.postprocess.postprocessing.postprocessor.common.sentiment.model.device_memory_snapshot import \
    DeviceMemorySnapshot
from process.core.postprocess.postprocessing.postprocessor.common.sentiment.type.event_types import SentimentLogEventType
from util.logging_util import logging_error_event


@dataclass(slots=True)
class BaseSentimentLog:

    # 내부적으로 사용되는 변수
    # 역직렬화에서 자식 클래스 구분 분기에 활용
    _TYPE_MAP: ClassVar[dict[SentimentLogEventType, Type[BaseSentimentLog]]] = {}

    # 역직렬화에서 자식 클래스 구분 분기의 기준이 되는 key (변수명과 반드시 일치해야 함)
    _EVENT_TYPE_CLASS_VAR_KEY: ClassVar[str] = "EVENT_TYPE"
    _EVENT_TYPE_KEY: ClassVar[str] = "event_type"

    # 클래스 선언 시 반드시 초기화해야 하는 변수
    EVENT_TYPE: ClassVar[SentimentLogEventType]

    # data class 변수
    event_type: SentimentLogEventType = field(init=False)
    timestamp: datetime

    # event_type 은 초기화 불가능이며, 해당 메서드를 통해서만 초기화
    def __post_init__(self):
        if not isinstance(self.EVENT_TYPE, SentimentLogEventType):
            raise TypeError(
                f"{self.__class__.__name__} 의 'EVENT_TYPE' 데이터는 반드시 'SentimentLogEventType' 이어야 합니다. "
                f"코드를 확인해주세요."
            )

        self.event_type = self.EVENT_TYPE

    # 해당 클래스를 상속 받는 자식 클래스들은 자신의 event type 을 type map 에 등록하게 되고, 
    # 이 type map 을 이용하여 직렬화/역직렬화 로직에 활용
    def __init_subclass__(cls, **kwargs):
        super(BaseSentimentLog, cls).__init_subclass__(**kwargs)

        event_type = getattr(cls, cls._EVENT_TYPE_CLASS_VAR_KEY, None)

        if isinstance(event_type, SentimentLogEventType):
            BaseSentimentLog._TYPE_MAP[event_type] = cls

    @classmethod
    def from_dict(cls, log_dict: dict) -> BaseSentimentLog:
        """
        직렬화 dict 데이터로부터 로그 객체 반환

        해당 객체가 관리하는 개별 변수들에 대해,
        선언된 type hint 로의 파싱을 보장

        :param log_dict: 직렬화 대상 dict
        :return: 직렬화된 BaseSentimentLog
        """

        log_dict = log_dict.copy()

        try:
            event_type = log_dict.get(cls._EVENT_TYPE_KEY)

            if isinstance(event_type, str):
                event_type = SentimentLogEventType(event_type)

            target_class = cls._TYPE_MAP.get(event_type)

            if target_class is None:
                raise ValueError(
                    f"로그 데이터의 BaseSentimentLog 객체 파싱 과정에서, 정의되지 않은 객체 타입 '{event_type}' 이 사용되었습니다. "
                    f"코드를 확인해주세요."
                )

            # init 이 금지된 변수 제외
            log_dict.pop(cls._EVENT_TYPE_KEY)

            # 해당 클래스 명세에 선언된 정보 가져오기
            class_type_hints = get_type_hints(target_class)
            deserialized_dict = {
                key: deserialize_log_value(value, class_type_hints.get(key, Any))
                for key, value in log_dict.items()
            }

            # 논리적으론 문제 없음 (init False 인 event 제외)
            # noinspection PyArgumentList
            return target_class(**deserialized_dict)

        except Exception as e:
            logging_error_event(
                exception_instance=e,
                log_message="While deserializing log data to BaseSentimentLog",
            )
            raise

    def to_json_dict(self) -> dict:
        """
        로그 객체로부터 직렬화용 dict 반환

        해당 객체가 관리하는 변수들의 타입 혹은 값을 직접 변경하지 않으면서
        JSON 직렬화가 가능한 형태의 dict 로 반환

        :return: 직렬화 가능 포맷으로 파싱된, 해당 객체가 관리하는 변수 및 값 dict
        """

        payload = asdict(self)

        return {
            key: serialize_log_value(value)
            for key, value in payload.items()
        }


@dataclass(slots=True)
class SentimentInferredLog(BaseSentimentLog):
    """
    감성 추론 결과 및 dynamic bucketing 관련 로그 정보 관리 클래스
    """

    EVENT_TYPE = SentimentLogEventType.INFERRED

    # batch
    batch_snapshot: BatchSnapshot

    # result
    positive_text_count: int
    negative_text_count: int

    # environment
    device: torch.device

    # performance
    elapsed_ms: float


@dataclass(slots=True)
class SentimentOOMFallbackLog(BaseSentimentLog):
    """
    감성 추론 중 발생한 OOM (Out-Of-Memory) 에러 fallback 관련 로그 정보 관리 클래스
    """

    EVENT_TYPE = SentimentLogEventType.OOM_FALLBACK

    # batch
    original_batch_snapshot_summary: BatchSnapshotSummary

    # fallback result batch
    fallback_batch_snapshot_summaries: list[BatchSnapshotSummary]

    # environment
    device: torch.device

    # error
    error_message: str

    # memory
    memory_snapshot: DeviceMemorySnapshot


@dataclass(slots=True)
class SentimentInferredFailedLog(BaseSentimentLog):
    """
    감성 추론 중 발생한 추론 실패 관련 로그 정보 관리 클래스
    """

    EVENT_TYPE = SentimentLogEventType.INFERRED_FAILED

    # bucket, batch
    batch_snapshot_summary: BatchSnapshotSummary

    # environment
    device: torch.device

    # error
    exception_type: str
    error_message: str

    # memory
    memory_snapshot: DeviceMemorySnapshot


@dataclass(slots=True)
class SentimentIntervalStatisticsLog(BaseSentimentLog):
    """
    구간별 감성 추론 결과의 연산 통계 데이터 관련 로그 정보 관리 클래스

    OOM, Fallback 등 실패 관련 로그를 제외한
    감성 추론에 성공한 데이터들에 대해서만 통계 데이터를 저장

    원칙적으로는 '마지막으로 연산된 통계 정보' 시점부터,
    현 시점까지 수집된 추론 데이터로 연산된 통계 정보의 구간을 의미한다
    """

    EVENT_TYPE = SentimentLogEventType.INFERRED_STATISTICS

    # progress
    inferred_total_text_count: int

    positive_text_count: int
    negative_text_count: int

    avg_text_length: float
    p95_text_length: int

    avg_token_length: float
    p95_token_length: int

    token_to_text_ratio: float

    # config
    applied_max_text_length: int
    applied_optimal_token_count_per_batch: int


@dataclass(slots=True)
class SentimentConfigTunerMetaLog(BaseSentimentLog):
    """
    감성 추론 관련 로그 분석에 대한 진행 상태 및 처리 이력에 대한 메타 데이터 정보 관리 클래스
    """

    EVENT_TYPE = SentimentLogEventType.CONFIG_TUNER_META

    # progress
    tuned_log_count: int

    last_read_file_byte_size: int
    last_read_cursor_byte: int
    last_tuned_log_timestamp: datetime


@dataclass(slots=True)
class SentimentConfigTunerStatisticsMetaLog(BaseSentimentLog):
    """
    감성 추론 결과의 누적 연산 통계 데이터 및
    감성 추론 관련 로그 분석에 대한 진행 상태 및 처리 이력에 대한 메타 데이터
    동시 관리 클래스
    """

    EVENT_TYPE = SentimentLogEventType.CONFIG_TUNER_STATISTICS_META

    sentiment_interval_statistics_log: SentimentIntervalStatisticsLog
    sentiment_config_tuner_meta_log: SentimentConfigTunerMetaLog
