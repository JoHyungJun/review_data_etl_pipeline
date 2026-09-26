"""
export_attribute_schema.py
--------------------------

메인 프로세스 파이프라인의 최종 결과물 포맷이 되는
VReview 이관 포맷 필수 컬럼을 정의해둔 상수 클래스 모듈

BaseAttributeSchema 에 선언된 전체 컬럼이 필수 컬럼 대상이 되며,
반드시 모든 컬럼을 포맷에 맞게 정의해야 함
"""


import re

from core.base.schema.attribute.base_export_attribute_schema import BaseExportAttributeSchema
from util.column_util import build_indexed_column_name


class VReviewExportAttributeSchema(BaseExportAttributeSchema):

    REVIEW_ID = '리뷰_id'
    PRODUCT_ID = '상품_id'

    REVIEW_CREATED_DATE = '리뷰_작성_일자'
    REVIEW_CREATED_TIME = '리뷰_작성_시간'
    REVIEW_WRITER_NAME = '리뷰_작성자명'
    REVIEW_TITLE = '리뷰_제목'
    REVIEW_CONTENTS = '리뷰_내용'
    REVIEW_STAR_RATING = '리뷰_별점'
    MANAGER_COMMENT = '관리자_댓글'

    PRODUCT_OPTION_NAME = '구매옵션_옵션명'
    PRODUCT_OPTION_VALUE = '구매옵션_옵션값'
    CUSTOMER_ATTRIBUTE_NAME = '고객정보_정보명'
    CUSTOMER_ATTRIBUTE_VALUE = '고객정보_답변값'
    URL_IMAGE = 'URL_이미지'
    URL_VIDEO = 'URL_동영상'

    INDEXED_COLUMNS_NESTED_FORMAT = {
        PRODUCT_OPTION_NAME: [PRODUCT_OPTION_NAME] * 10,
        PRODUCT_OPTION_VALUE: [PRODUCT_OPTION_VALUE] * 10,
        CUSTOMER_ATTRIBUTE_NAME: [CUSTOMER_ATTRIBUTE_NAME] * 10,
        CUSTOMER_ATTRIBUTE_VALUE: [CUSTOMER_ATTRIBUTE_VALUE] * 10,
        URL_IMAGE: [URL_IMAGE] * 10,
        URL_VIDEO: [URL_VIDEO] * 10,
    }

    @classmethod
    def get_ordered_flatten_constants_value(cls) -> list[str]:
        flatten_columns = cls.get_flatten_constants_name_value_mapping().values()

        # indexed 컬럼 제거 대상 정규식
        indexed_column_patterns = [
            rf"^{cls.PRODUCT_OPTION_NAME}\d+$",
            rf"^{cls.PRODUCT_OPTION_VALUE}\d+$",
            rf"^{cls.CUSTOMER_ATTRIBUTE_NAME}\d+$",
            rf"^{cls.CUSTOMER_ATTRIBUTE_VALUE}\d+$",
        ]

        # '구매옵션_옵션명/옵션값', '고객정보_정보명/답변값' indexed 컬럼 제거
        reordered_columns = [
            column
            for column in flatten_columns
            if not any(
                re.match(pattern, column)
                for pattern in indexed_column_patterns
            )
        ]

        # 순서에 맞게 indexed 컬럼 mix
        mixed_indexed_columns = []

        # '구매옵션_옵션명/옵션값'
        for index in range(1, 11):
            mixed_indexed_columns.append(
                build_indexed_column_name(
                    column_name=cls.PRODUCT_OPTION_NAME,
                    index=index,
                )
            )

            mixed_indexed_columns.append(
                build_indexed_column_name(
                    column_name=cls.PRODUCT_OPTION_VALUE,
                    index=index,
                )
            )

        # '고객정보_정보명/답변값'
        for index in range(1, 11):
            mixed_indexed_columns.append(
                build_indexed_column_name(
                    column_name=cls.CUSTOMER_ATTRIBUTE_NAME,
                    index=index,
                )
            )

            mixed_indexed_columns.append(
                build_indexed_column_name(
                    column_name=cls.CUSTOMER_ATTRIBUTE_VALUE,
                    index=index,
                )
            )

        # '관리자_댓글' 컬럼 뒤에 삽입
        try:
            manager_comment_index = reordered_columns.index(cls.MANAGER_COMMENT)

            reordered_columns[
                manager_comment_index + 1:
                manager_comment_index + 1
            ] = mixed_indexed_columns

        # '관리자_댓글' 컬럼이 없으면 마지막 위치에 추가
        except ValueError:
            reordered_columns.extend(mixed_indexed_columns)

        return reordered_columns
