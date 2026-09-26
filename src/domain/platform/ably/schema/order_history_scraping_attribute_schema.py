"""
order_history_scraping_attribute_schema.py
------------------------------------------

A-bly order history scraping API 의 추출 및 매핑/save 대상 컬럼을 정의해둔 상수 클래스 모듈

BaseAttributeSchema 의 필수 컬럼 및 추가적인 save 대상 컬럼 정의
"""


from core.base.schema.attribute.base_order_history_attribute_schema import BaseOrderHistoryAttributeSchema


class AblyOrderHistoryScrapingReviewAttributeSchema(BaseOrderHistoryAttributeSchema):

    ORDER_ID = "주문_id"
    PRODUCT_ID = "상품_id"

    BUYER_NAME = "구매자명"
    BUYER_PHONE = "구매자_번호"
    BUYER_EMAIL = "구매자_이메일"

    RECEIVER_NAME = "수취인명"
    RECEIVER_ADDR = "수취인_주소"
    GOODS_NAME = "판매명"
    GOODS_CUSTOM_CODE = "상품_코드"
    OPTION_INFO = "옵션_정보"
    ORDERED_AT = "주문_일시"
