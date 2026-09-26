"""
device_memory_snapshot.py
-------------------------

runtime 호스트 머신 기준, 특정 시점에서의 메모리 상태 정보 관리 클래스 모듈
"""


from dataclasses import dataclass

from process.core.postprocess.postprocessing.postprocessor.common.sentiment.type.device_types import DeviceType
from process.core.postprocess.postprocessing.postprocessor.common.sentiment.type.memory_types import (
    MemoryMeasurementConfidenceType,
    MemoryMeasurementMethodType,
)


@dataclass(slots=True)
class DeviceMemorySnapshot:
    device_type: DeviceType

    available_memory_bytes: float

    memory_measurement_confidence: MemoryMeasurementConfidenceType
    memory_measurement_method: MemoryMeasurementMethodType
