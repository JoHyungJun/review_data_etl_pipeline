"""
attribute_schema_meta.py
--------------------------

BaseAttributeSchema 의 기본 규칙이 되는 
RequiredConstantsMeta, UniqueValueConstantsMeta 두 메타 클래스를 합성한 메타 클래스
"""


from core.base.meta.required_constants_meta import RequiredConstantsMeta
from core.base.meta.unique_value_constants_meta import UniqueValueConstantsMeta


class AttributeSchemaMeta(RequiredConstantsMeta, UniqueValueConstantsMeta):
    pass
