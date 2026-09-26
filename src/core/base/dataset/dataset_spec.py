"""
dataset_spec.py
---------------

데이터셋의 정보를 관리하기 위한 추상 클래스 모듈

해당 클래스는 특정 데이터 단위에 대한 전반적인 정보를 관리하며, 다음과 같은 두 객체 정보를 가지고 있음
- attribute_schema:
    해당 데이터셋의 컬럼명을 상수로 가지고 있는 BaseAttributeSchema
- load_spec:
    해당 데이터셋의 save 위치 정보 (path) 와 해당 데이터셋에서 불러올 데이터에 대한 조건 정보 (query) 를 가지고 있는 BaseStorageLoadSpec
"""


from dataclasses import dataclass
from typing import Type, Generic

from core.base.storage.spec.base_load_spec import BaseStorageLoadSpec
from core.base.type.generic_types import TBaseAttributeSchema


@dataclass(frozen=True)
class DatasetSpec(Generic[TBaseAttributeSchema]):
    attribute_schema: Type[TBaseAttributeSchema]
    load_spec: BaseStorageLoadSpec
