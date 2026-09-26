"""
id_mapping_attribute_schema.py
------------------------------

{VReview 상품 id - A-bly 상품 id} 정보 관련 매핑 대상 필수 컬럼을 정의해둔 상수 클래스 모듈
"""


from core.base.schema.attribute.base_product_id_mapping_attribute_schema import \
    BaseProductIdMappingAttributeSchema


class AblyVReviewProductIdMappingAttributeSchema(BaseProductIdMappingAttributeSchema):

    SCRAPING_PLATFORM_PRODUCT_ID = "에이블리_상품_id"
    EXPORT_PLATFORM_PRODUCT_ID = "브이리뷰_상품_id"
