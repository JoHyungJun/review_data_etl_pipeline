"""
ably_rule.py
------------

VReview 포맷 기준, A-bly 의 포맷 및 데이터에서만 해당하는 추가적인 데이터 전처리 로직을 관리하는 모듈
"""


import pandas as pd

from domain.export.vreview.schema.export.export_attribute_schema import VReviewExportAttributeSchema
from process.core.preprocess.preprocessing.model.context.source_data_context import SourceDataContext


def ably_to_vreview_preprocessing(
        export_formatted_df: pd.DataFrame,
        source_data_context: SourceDataContext,
) -> pd.DataFrame:
    # unpack & init attribute schemas
    joined_df = source_data_context.joined_df
    order_history_attribute_schema = source_data_context.order_history_attribute_schema

    vreview_attribute_schema = VReviewExportAttributeSchema

    # validate
    if order_history_attribute_schema is None or vreview_attribute_schema is None:
        return export_formatted_df

    # df copy
    export_preprocessed_df = export_formatted_df.copy()

    # preprocessing
    # 리뷰 작성자명 컬럼을 구매자명 컬럼으로 대체
    if (
            order_history_attribute_schema.BUYER_NAME is None
            or vreview_attribute_schema.REVIEW_WRITER_NAME is None
            or order_history_attribute_schema.BUYER_NAME not in joined_df.columns
    ):
        return export_formatted_df

    export_preprocessed_df[vreview_attribute_schema.REVIEW_WRITER_NAME] \
        = joined_df[order_history_attribute_schema.BUYER_NAME]

    return export_preprocessed_df
