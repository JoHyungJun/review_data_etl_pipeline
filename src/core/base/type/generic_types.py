"""
generic_types.py
----------------

제네릭 변수들을 선언 및 관리하기 위한 모듈
"""


from typing import TypeVar

from core.base.schema.attribute.base_attribute_schema import BaseAttributeSchema
from core.base.schema.attribute.base_export_attribute_schema import BaseExportAttributeSchema


TBaseAttributeSchema = TypeVar("TBaseAttributeSchema", bound=BaseAttributeSchema)

TExportAttributeSchema = TypeVar("TExportAttributeSchema", bound=BaseExportAttributeSchema)
