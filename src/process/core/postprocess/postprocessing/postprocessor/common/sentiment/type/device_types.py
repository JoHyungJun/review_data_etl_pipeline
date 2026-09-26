"""
device_types.py
---------------

감성 추론 로직에서의 torch device 관련 상수 정의 Enum 모듈

믹스인 (Mixin) 클래스로 정의되었으므로, .value 없이 값 사용 가능
"""


from enum import Enum


class DeviceType(str, Enum):
    CUDA = "cuda"
    MPS = "mps"
    XPU = "xpu"
    CPU = "cpu"
