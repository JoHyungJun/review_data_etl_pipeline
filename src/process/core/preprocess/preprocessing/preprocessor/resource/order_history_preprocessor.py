"""
order_history_preprocessor.py
-----------------------------

주문 내역 데이터 포맷팅/파싱/컬럼 검증 관련 preprocessor 모듈
"""


import logging
from pathlib import Path
from typing import Type, Optional, Union

import pandas as pd

from core.base.schema.attribute.base_attribute_schema import BaseAttributeSchema
from core.base.schema.attribute.base_order_history_attribute_schema import BaseOrderHistoryAttributeSchema
from core.base.schema.attribute.util.attribute_schema_util import build_attribute_mapping
from util.column_util import rename_safely, drop_invalid_columns_data_safely, parse_number_columns_to_int_str_safely, \
    reindex_safely


def order_history_preprocessing(
        order_history_df: pd.DataFrame,
        source_attribute_schema: Type[BaseOrderHistoryAttributeSchema],
        target_attribute_schema: Optional[Type[BaseAttributeSchema]] = None,
        file_path: Optional[Union[Path, str]] = None,
) -> pd.DataFrame:
    """
    수집된 주문 내역 데이터 전처리 및 DataFrame 반환

    order_history_scraping.py 모듈의 산출물 포맷 및 컬럼명을 기준으로 동작

    - 필수 컬럼 추출, 누락값 제거, 자료형 변환
    - source attribute schema 에 선언되지 않은 컬럼 탈락
    - 컬럼명 rename (Optional)

    :param order_history_df: 주문 내역 데이터 pandas.DataFrame
    :param source_attribute_schema: 주문 내역 데이터의 컬럼명 정보를 담은 BaseReviewAttributeSchema
    :param target_attribute_schema: 매핑할 컬럼명 정보를 담은 BaseAttributeSchema (Optional)
    :param file_path: 로그를 위한 파일 경로 Optional[Union[Path, str]]
    :return: 전처리된 주문 내역 데이터 pandas.DataFrame
    """

    order_history_mapping_schema = source_attribute_schema

    # 컬럼명 매핑
    if target_attribute_schema is not None:
        order_history_mapping_dict, order_history_mapping_schema = build_attribute_mapping(
            source_schema=source_attribute_schema,
            target_schema=target_attribute_schema,
        )

        order_history_df = rename_safely(df=order_history_df, column_name_mapping=order_history_mapping_dict)

    # 필수 컬럼 추출, 누락값 제거, 자료형 변환
    drop_invalid_columns_data_safely(
        df=order_history_df,
        column_names=[
            order_history_mapping_schema.ORDER_ID,
            order_history_mapping_schema.PRODUCT_ID,
        ],
    )
    parse_number_columns_to_int_str_safely(
        df=order_history_df,
        column_names=[
            order_history_mapping_schema.ORDER_ID,
            order_history_mapping_schema.PRODUCT_ID,
        ],
    )

    # source attribute schema 에 선언되지 않은 컬럼 탈락
    indexed_order_history_df = reindex_safely(
        df=order_history_df,
        column_names=order_history_mapping_schema.get_flatten_constants_name_value_mapping().values(),
    )

    eliminated_columns = set(order_history_df.columns) - set(indexed_order_history_df.columns)
    if eliminated_columns:
        logging.warning(
            f"[FORMAT] target_df=review_df, target_attribute={order_history_mapping_schema.__name__}, "
            f"eliminated_columns={eliminated_columns}: "
            f"Some columns eliminated while reindexing"
        )

    logging.debug(f"[FORMAT] target_df=order_history_df"
                  f"{f', file_path={file_path}' if file_path is not None else ''}")

    return indexed_order_history_df
