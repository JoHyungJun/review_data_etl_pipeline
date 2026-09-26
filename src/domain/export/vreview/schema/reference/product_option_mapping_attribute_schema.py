"""
product_option_mapping_attribute_schema.py
------------------------------------------

{VReview 상품 id - 상품명, 옵션명} 정보 관련 매핑 대상 필수 컬럼을 정의해둔 상수 클래스 모듈
"""


from core.base.schema.attribute.base_product_option_mapping_attribute \
    import BaseProductOptionMappingAttributeSchema


class VReviewProductOptionMappingAttributeSchema(BaseProductOptionMappingAttributeSchema):

    EXPORT_PLATFORM_PRODUCT_ID = "브이리뷰_상품_id"
    PRODUCT_NAME = "상품명"

    PRODUCT_OPTION_NAME = "옵션명"
