"""
vreview_preprocessor.py
-----------------------

VReview 최종 결과물 포맷 관련 preprocessing 모듈

로직에 활용되는 df 컬럼 혹은 개별 상수의 검증 (is not None) 은
BaseAttributeSchema 의 metaclass 규칙 혹은 개별 메서드에 내장된 검증 로직으로 대체

메서드 내부에서 사용되는 attribute schema 는 다음과 같은 규칙을 가짐
- canonical attribute schema: join 이후 rename 의 기준이 되는 컬럼 attribute schema (내부 선언)
- export attribute schema: export 대상이 되는 플랫폼의 attribute schema (내부 선언)
- 그 외의 attribute schema: 동적인 플랫폼 의존적 컬럼 attribute schema (파라미터)
"""


import pandas as pd

from domain.export.vreview.schema.export.export_attribute_schema import VReviewExportAttributeSchema
from domain.platform.platform import Platform
from process.core.preprocess.preprocessing.model.context.source_data_context import SourceDataContext
from process.core.preprocess.preprocessing.preprocessor.common.datetime_preprocessor import (
    split_datetime_column,
    parse_date_time_column,
)
from process.core.preprocess.preprocessing.preprocessor.export.common.orchestration.export_rule_applier import export_rule_applier
from util.column_util import combine_title_content, build_indexed_column_name, drop_invalid_columns_data_safely


def vreview_export_preprocessing(
        target_platform: Platform,
        export_formatted_df: pd.DataFrame,
        source_data_context: SourceDataContext,
) -> pd.DataFrame:
    # unpack & init attribute schemas
    (
        review_attribute_schema,
        order_history_attribute_schema,
        product_id_mapping_attribute_schema,
        product_option_mapping_attribute_schema,
        joined_df,
    ) = source_data_context.unpack()

    export_attribute_schema = VReviewExportAttributeSchema

    # df copy
    joined_preprocessed_df = joined_df.copy()
    export_preprocessed_df = export_formatted_df.copy()

    # canonical schema preprocessing
    # 날짜/시간
    if (
            export_attribute_schema.REVIEW_CREATED_DATE is None
            or export_attribute_schema.REVIEW_CREATED_TIME is None
    ):
        raise ValueError("VReview 포맷팅 중 날짜/시간 관련 데이터에서 문제를 발견했습니다. 데이터 및 코드를 확인해주세요.")
    
    # 날짜/시간 분리 & 파싱
    if (
            review_attribute_schema.REVIEW_CREATED_DATETIME is not None
            and review_attribute_schema.REVIEW_CREATED_DATETIME in joined_preprocessed_df.columns
    ):
        # split_datetime_column() 은 내부적으로 날짜/시간 파싱까지 담당
        joined_preprocessed_df = split_datetime_column(
            df=joined_preprocessed_df,
            datetime_column_name=review_attribute_schema.REVIEW_CREATED_DATETIME,
            target_date_column_name=export_attribute_schema.REVIEW_CREATED_DATE,
            target_time_column_name=export_attribute_schema.REVIEW_CREATED_TIME,
        )

        export_preprocessed_df[export_attribute_schema.REVIEW_CREATED_DATE] \
            = joined_preprocessed_df[export_attribute_schema.REVIEW_CREATED_DATE]

        export_preprocessed_df[export_attribute_schema.REVIEW_CREATED_TIME] \
            = joined_preprocessed_df[export_attribute_schema.REVIEW_CREATED_TIME]

    else:
        export_preprocessed_df = parse_date_time_column(
            df=export_preprocessed_df,
            date_column_name=export_attribute_schema.REVIEW_CREATED_DATE,
            time_column_name=export_attribute_schema.REVIEW_CREATED_TIME,
        )

    # 별점 처리
    export_preprocessed_df[export_attribute_schema.REVIEW_STAR_RATING] = (
        export_preprocessed_df[export_attribute_schema.REVIEW_STAR_RATING].replace("", pd.NA).fillna(5)
        if (
                export_attribute_schema.REVIEW_STAR_RATING is not None
                and export_attribute_schema.REVIEW_STAR_RATING in export_preprocessed_df.columns
        )
        else 5
    )

    # 상품 id
    export_preprocessed_df[export_attribute_schema.PRODUCT_ID] \
        = joined_preprocessed_df[product_id_mapping_attribute_schema.EXPORT_PLATFORM_PRODUCT_ID]

    # export schema preprocessing
    # 고객 정보
    export_preprocessed_df[build_indexed_column_name(export_attribute_schema.CUSTOMER_ATTRIBUTE_NAME, 1)] = '구매처'
    export_preprocessed_df[build_indexed_column_name(export_attribute_schema.CUSTOMER_ATTRIBUTE_VALUE, 1)] = \
        f'{target_platform.get_platform_kor_name()} 구매자 리뷰입니다.'

    # 리뷰 내용이 없는 컬럼 제거
    drop_invalid_columns_data_safely(
        df=export_preprocessed_df,
        column_names=[
            export_attribute_schema.REVIEW_CONTENTS,
        ],
    )

    # 리뷰 내용 내에 리뷰 제목 포함
    if (
            export_attribute_schema.REVIEW_TITLE is not None
            and export_attribute_schema.REVIEW_TITLE in export_preprocessed_df.columns
            and export_attribute_schema.REVIEW_CONTENTS is not None
            and export_attribute_schema.REVIEW_CONTENTS in export_preprocessed_df.columns

    ):
        export_preprocessed_df[export_attribute_schema.REVIEW_CONTENTS] = export_preprocessed_df.apply(
            lambda row: combine_title_content(
                row,
                export_attribute_schema.REVIEW_TITLE,
                export_attribute_schema.REVIEW_CONTENTS,
            ),
            axis=1,
        )
        export_preprocessed_df[export_attribute_schema.REVIEW_TITLE] = None

    # 구매 정보
    export_preprocessed_df[build_indexed_column_name(export_attribute_schema.PRODUCT_OPTION_NAME, 1)] = \
        joined_preprocessed_df[product_option_mapping_attribute_schema.PRODUCT_NAME]
    export_preprocessed_df[build_indexed_column_name(export_attribute_schema.PRODUCT_OPTION_VALUE, 1)] = \
        joined_preprocessed_df[product_option_mapping_attribute_schema.PRODUCT_OPTION_NAME]

    # target to export preprocessing
    target_preprocessed_df = export_rule_applier(
        export_formatted_df=export_preprocessed_df,
        source_data_context=source_data_context,
        export_platform=Platform.VREVIEW,
        target_platform=target_platform,
    )

    return target_preprocessed_df
