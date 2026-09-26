"""
memory_types.py
---------------

감성 추론 로직에서 활용되는 device 별 메모리 연산 방식 및 연산 정확도 관련 상수 정의 Enum 모듈

믹스인 (Mixin) 클래스로 정의되었으므로, .value 없이 값 사용 가능
"""


from enum import Enum

from process.core.postprocess.postprocessing.postprocessor.common.sentiment.type.device_types import DeviceType


class MemoryMeasurementConfidenceType(str, Enum):
    # 라이브러리 활용 혹은 명확한 로직의 연산 등을 통해 명확히 계산된 값
    EXACT = "exact"
    
    # 추정치
    ESTIMATED = "estimated"

    # 측정 실패 (메모리 연산을 지원하는 라이브러리가 없거나, 추정치 로직도 작성할 수 없는 상태)
    UNAVAILABLE = "unavailable"


class MemoryMeasurementMethodType(str, Enum):
    CUDA_API = "cuda_api"
    XPU_API = "xpu_api"
    PSUTIL = "psutil"

    # 측정 실패 후 로직에 작성된 임의의 최소 메모리 반환
    HARDCODED_DEFAULT = "hardcoded_default"
