"""
id_mapping_attribute_schema.py
------------------------------

{VReview 상품 id - Coupang 상품 id} 정보 관련 매핑 대상 필수 컬럼을 정의해둔 상수 클래스 모듈
"""


from core.base.schema.attribute.base_product_id_mapping_attribute_schema import \
    BaseProductIdMappingAttributeSchema


class CoupangVReviewProductIdMappingAttributeSchema(BaseProductIdMappingAttributeSchema):

    SCRAPING_PLATFORM_PRODUCT_ID = "노출상품ID"
    EXPORT_PLATFORM_PRODUCT_ID = "브이리뷰_상품_id"
