"""
review_scraping_attribute_schema.py
-----------------------------------

VReview review scraping API 의 추출 및 매핑/save 대상 컬럼을 정의해둔 상수 클래스 모듈

BaseAttributeSchema 의 필수 컬럼 및 추가적인 save 대상 컬럼 정의
"""


from core.base.schema.attribute.base_review_attribute_schema import BaseReviewAttributeSchema


class VReviewReviewScrapingReviewAttributeSchema(BaseReviewAttributeSchema):

    REVIEW_ID = "리뷰_id"
    REVIEW_CONTENTS = "리뷰_내용"

    REVIEW_CREATED_DATETIME = "리뷰_작성_일시"
    REVIEW_WRITER_NAME = "작성자명"

    PRODUCT_ID = "상품_내부_id"

    IS_VISIBLE = "리뷰_노출_여부"
    PRODUCT_REMOTE_ID = "상품_노출_id"
    PRODUCT_NAME = "상품명"
    REVIEW_GROUP_ID = "그룹_id"
    REVIEW_GROUP_NAME = "그룹명"
    QUESTION = "고객정보_정보명"
    ANSWER = "고객정보_답변값"
