"""
coupang_rule.py
---------------

VReview 포맷 기준, Coupang 의 포맷 및 데이터에서만 해당하는 추가적인 데이터 전처리 로직을 관리하는 모듈
"""


import pandas as pd

from domain.export.vreview.schema.export.export_attribute_schema import VReviewExportAttributeSchema
from process.core.preprocess.preprocessing.model.context.source_data_context import SourceDataContext


def coupang_to_vreview_preprocessing(
        export_formatted_df: pd.DataFrame,
        source_data_context: SourceDataContext,
) -> pd.DataFrame:
    # unpack & init attribute schemas
    joined_df = source_data_context.joined_df

    vreview_attribute_schema = VReviewExportAttributeSchema

    # validate
    if vreview_attribute_schema is None:
        return export_formatted_df

    # df copy
    export_preprocessed_df = export_formatted_df.copy()

    # preprocessing
    # 리뷰_별점 컬럼을 5 점으로 바꿈 (비즈니스 로직)
    export_preprocessed_df[vreview_attribute_schema.REVIEW_STAR_RATING] = 5

    return export_preprocessed_df
