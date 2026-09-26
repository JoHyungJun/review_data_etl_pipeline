"""
base_export_attribute_schema.py
-------------------------------

최종 산출물 포맷의 공통 컬럼 규칙을 정의하는 추상 클래스 모듈

최종 산출물 포맷은 반드시 컬럼 순서대로 상수를 정의해야 함
"""


from core.base.schema.attribute.base_attribute_schema import BaseAttributeSchema


class BaseExportAttributeSchema(BaseAttributeSchema):
    pass
