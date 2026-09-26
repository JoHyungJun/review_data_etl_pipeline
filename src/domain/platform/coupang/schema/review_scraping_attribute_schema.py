"""
review_scraping_attribute_schema.py
-----------------------------------

Coupang review scraping API 의 추출 및 매핑/save 대상 컬럼을 정의해둔 상수 클래스 모듈

BaseAttributeSchema 의 필수 컬럼 및 추가적인 save 대상 컬럼 정의
"""


from core.base.schema.attribute.base_review_attribute_schema import BaseReviewAttributeSchema


class CoupangReviewScrapingReviewAttributeSchema(BaseReviewAttributeSchema):

    REVIEW_ID = "리뷰_id"
    REVIEW_CONTENTS = "리뷰_내용"

    REVIEW_CREATED_DATETIME = "리뷰_작성_일시"
    REVIEW_WRITER_NAME = "구매자명"
    REVIEW_TITLE = "리뷰_제목"
    REVIEW_STAR_RATING = "별점"

    URL_IMAGE = "URL_이미지"

    PRODUCT_ID = "상품_노출_id"

    ITEM_NAME = "판매명"
    PRODUCT_OPTION_ID = "상품_옵션_id"
