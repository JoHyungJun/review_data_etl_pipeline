"""
event_types.py
--------------

감성 추론 로그에서의 이벤트 성격 관련 기준 정의 Enum 모듈
"""


from enum import StrEnum


class SentimentLogEventType(StrEnum):
    INFERRED = "inferred"
    OOM_FALLBACK = "oom_fallback"
    INFERRED_FAILED = "inferred_failed"

    INFERRED_STATISTICS = "inferred_statistics"
    CONFIG_TUNER_META = "config_tuner_meta"

    CONFIG_TUNER_STATISTICS_META = "config_tuner_statistics_meta"
