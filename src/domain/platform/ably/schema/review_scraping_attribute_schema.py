"""
review_scraping_attribute_schema.py
-----------------------------------

A-bly review scraping API 의 추출 및 매핑/save 대상 컬럼을 정의해둔 상수 클래스 모듈

BaseAttributeSchema 의 필수 컬럼 및 추가적인 save 대상 컬럼 정의
"""


from core.base.schema.attribute.base_review_attribute_schema import BaseReviewAttributeSchema


class AblyReviewScrapingReviewAttributeSchema(BaseReviewAttributeSchema):

    REVIEW_ID = "리뷰_id"
    REVIEW_CONTENTS = "리뷰_내용"
    PRODUCT_ID = "상품_id"

    REVIEW_CREATED_DATETIME = "리뷰_작성_일시"

    URL_IMAGE = "URL_이미지"

    ORDER_ID = "주문_id"

    PRODUCT_SIZE = "사이즈"

    INDEXED_COLUMNS_NESTED_FORMAT = {
        URL_IMAGE: [URL_IMAGE] * 10,
    }
