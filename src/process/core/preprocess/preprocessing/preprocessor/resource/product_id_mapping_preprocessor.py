"""
product_id_mapping_preprocessor.py
----------------------------------

export 플랫폼에 등록된 상품 id 와 상품 정보 매핑 데이터 포맷팅/파싱/컬럼 검증 관련 preprocessor 모듈
"""


import logging
from pathlib import Path
from typing import Type, Optional, Union

import pandas as pd

from core.base.schema.attribute.base_attribute_schema import BaseAttributeSchema
from core.base.schema.attribute.base_product_id_mapping_attribute_schema import \
    BaseProductIdMappingAttributeSchema
from core.base.schema.attribute.util.attribute_schema_util import build_attribute_mapping
from util.column_util import rename_safely, drop_invalid_columns_data_safely, parse_number_columns_to_int_str_safely, \
    reindex_safely


def platform_to_export_product_id_mapping_preprocessing(
        product_id_mapping_df: pd.DataFrame,
        source_attribute_schema: Type[BaseProductIdMappingAttributeSchema],
        target_attribute_schema: Optional[Type[BaseAttributeSchema]] = None,
        file_path: Optional[Union[Path, str]] = None,
) -> pd.DataFrame:
    """
    리뷰가 수집된 플랫폼 기준 상품 id 와 export 플랫폼에 등록된 상품 id 매핑 정보 데이터 전처리 및 DataFrame 반환

    - 필수 컬럼 추출, 누락값 제거, 자료형 변환
    - source attribute schema 에 선언되지 않은 컬럼 탈락
    - 컬럼명 rename (Optional)

    :param product_id_mapping_df: {리뷰 플랫폼 기준 상품 id - export 플랫폼별 상품 id} 매핑 데이터 pandas.DataFrame
    :param source_attribute_schema: 매핑 데이터의 컬럼명 정보를 담은 BaseReviewAttributeSchema
    :param target_attribute_schema: 매핑할 컬럼명 정보를 담은 BaseAttributeSchema (Optional)
    :param file_path: 로그를 위한 파일 경로 Optional[Union[Path, str]]
    :return: 전처리된 상품 id 매핑 데이터 pandas.DataFrame
    """

    id_mapping_schema = source_attribute_schema

    # 컬럼명 매핑
    if target_attribute_schema is not None:
        id_mapping_dict, id_mapping_schema = build_attribute_mapping(
            source_schema=source_attribute_schema,
            target_schema=target_attribute_schema,
        )

        product_id_mapping_df = rename_safely(df=product_id_mapping_df, column_name_mapping=id_mapping_dict)

    # 필수 컬럼 추출, 누락값 제거, 자료형 변환
    drop_invalid_columns_data_safely(
        df=product_id_mapping_df,
        column_names=[
            id_mapping_schema.SCRAPING_PLATFORM_PRODUCT_ID,
            id_mapping_schema.EXPORT_PLATFORM_PRODUCT_ID,
        ],
    )
    parse_number_columns_to_int_str_safely(
        df=product_id_mapping_df,
        column_names=[
            id_mapping_schema.SCRAPING_PLATFORM_PRODUCT_ID,
            id_mapping_schema.EXPORT_PLATFORM_PRODUCT_ID,
        ],
    )

    # source attribute schema 에 선언되지 않은 컬럼 탈락
    indexed_product_id_mapping_df = reindex_safely(
        df=product_id_mapping_df,
        column_names=id_mapping_schema.get_flatten_constants_name_value_mapping().values(),
    )

    eliminated_columns = set(product_id_mapping_df.columns) - set(indexed_product_id_mapping_df.columns)
    if eliminated_columns:
        logging.warning(
            f"[FORMAT] target_df=review_df, target_attribute={id_mapping_schema.__name__}, "
            f"eliminated_columns={eliminated_columns}: "
            f"Some columns eliminated while reindexing"
        )

    logging.debug(f"[FORMAT] target_df=vreview_id_df"
                  f"{f', file_path={file_path}' if file_path is not None else ''}")

    return indexed_product_id_mapping_df
