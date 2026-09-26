"""
transformation_spec.py
----------------------

데이터셋의 정보 및 컬럼명 변환 정보를 관리하기 위한 추상 클래스 모듈

해당 클래스는 특정 데이터 단위에 대한 전반적인 정보와 변환될 컬럼명 정보를 관리하며, 다음과 같은 두 객체 정보를 가지고 있음
- source_dataset: 특정 데이터 단위에 대한 save 위치/데이터 조건 정보와 컬럼명 정보를 가지고 있는
- target_attribute_schema: 변환 대상이 되는 타겟 데이터셋의 컬럼명을 상수로 가지고 있는 BaseAttributeSchema

get_attribute_mapping() 의 경우, 개별 객체가 관리하는 source/target BaseAttributeSchema 에 따라
컬럼명 변환 (rename) 에 필요한 mapping dict 를 반환하며,
@cached_property 캐싱을 통해 최초 계산 후엔 재사용
"""


from dataclasses import dataclass
from functools import cached_property
from typing import Type, Generic

from core.base.dataset.dataset_spec import DatasetSpec
from core.base.schema.attribute.base_attribute_schema import BaseAttributeSchema
from core.base.type.generic_types import TBaseAttributeSchema
from core.base.schema.attribute.util.attribute_schema_util import build_attribute_mapping


@dataclass(frozen=True)
class TransformationSpec(Generic[TBaseAttributeSchema]):
    source_dataset_spec: DatasetSpec[TBaseAttributeSchema]
    target_attribute_schema: Type[TBaseAttributeSchema]

    @cached_property
    def attribute_mapping(self) -> tuple[dict[str, str], Type[BaseAttributeSchema]]:
        return build_attribute_mapping(
            source_schema=self.source_dataset_spec.attribute_schema,
            target_schema=self.target_attribute_schema,
        )
