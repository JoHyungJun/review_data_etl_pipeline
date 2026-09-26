"""
base_spec.py
------------

저장소 (storage) save/load 에 활용할 쿼리 관련 공통 속성 클래스 설정 모듈
"""


from abc import ABC

from dataclasses import dataclass


@dataclass(frozen=True)
class BaseQuerySpec(ABC):
    pass
