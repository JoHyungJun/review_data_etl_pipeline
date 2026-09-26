"""
review_preprocessor.py
----------------------

리뷰 데이터 포맷팅/파싱/컬럼 검증 관련 preprocessor 모듈
"""


import logging
from pathlib import Path
from typing import Type, Optional, Union

import pandas as pd

from core.base.schema.attribute.base_attribute_schema import BaseAttributeSchema
from core.base.schema.attribute.base_review_attribute_schema import BaseReviewAttributeSchema
from core.base.schema.attribute.util.attribute_schema_util import build_attribute_mapping
from util.column_util import rename_safely, drop_invalid_columns_data_safely, parse_number_columns_to_int_str_safely, \
    reindex_safely


def review_preprocessing(
        review_df: pd.DataFrame,
        source_attribute_schema: Type[BaseReviewAttributeSchema],
        target_attribute_schema: Optional[Type[BaseAttributeSchema]] = None,
        file_path: Union[str, Path] = None,
) -> pd.DataFrame:
    """
    수집된 리뷰 데이터 전처리 및 DataFrame 반환

    review_scraping.py 모듈의 산출물 포맷 및 컬럼명을 기준으로 동작

    - 필수 컬럼 추출, 누락값 제거, 자료형 변환
    - source attribute schema 에 선언되지 않은 컬럼 탈락
    - 컬럼명 rename (Optional)

    :param review_df: 리뷰 데이터 pandas.DataFrame
    :param source_attribute_schema: 리뷰 데이터의 컬럼명 정보를 담은 BaseReviewAttributeSchema
    :param target_attribute_schema: 매핑할 컬럼명 정보를 담은 BaseAttributeSchema (Optional)
    :param file_path: 로그를 위한 파일 경로 (Optional)
    :return: 전처리된 리뷰 데이터 pandas.DataFrame
    """

    review_mapping_schema = source_attribute_schema

    # 컬럼명 매핑
    if target_attribute_schema is not None:
        review_mapping_dict, review_mapping_schema = build_attribute_mapping(
            source_schema=source_attribute_schema,
            target_schema=target_attribute_schema,
        )

        review_df = rename_safely(df=review_df, column_name_mapping=review_mapping_dict)

    # 필수 컬럼 추출, 누락값 제거, 자료형 변환
    drop_invalid_columns_data_safely(
        df=review_df,
        column_names=[
            review_mapping_schema.REVIEW_ID,
            review_mapping_schema.ORDER_ID,
            review_mapping_schema.PRODUCT_ID,
        ],
    )
    parse_number_columns_to_int_str_safely(
        df=review_df,
        column_names=[
            review_mapping_schema.REVIEW_ID,
            review_mapping_schema.ORDER_ID,
            review_mapping_schema.PRODUCT_ID,
        ],
    )

    # source attribute schema 에 선언되지 않은 컬럼 탈락
    indexed_review_df = reindex_safely(
        df=review_df,
        column_names=review_mapping_schema.get_flatten_constants_name_value_mapping().values(),
    )

    eliminated_columns = set(review_df.columns) - set(indexed_review_df.columns)
    if eliminated_columns:
        logging.warning(
            f"[FORMAT] target_df=review_df, target_attribute={review_mapping_schema.__name__}, "
            f"eliminated_columns={eliminated_columns}: "
            f"Some columns eliminated while reindexing"
        )

    logging.debug(f"[FORMAT] target_df=review_df" 
                  f"{f', file_path={file_path}' if file_path is not None else ''}")

    return indexed_review_df
