"""
product_option_remapping.py
---------------------------

상품 id 를 기준으로 잘못 매핑되어 있던 상품 정보 (상품명, 옵션명) 를 올바른 데이터로 다시 매핑하는 모듈

옵션 변경을 통해 다른 상품을 구매할 수 있는 플랫폼이 존재함
(ex. A 상품 구매 페이지에서 옵션을 B 상품으로 바꾸면,
     실제 구매 상품은 B 이지만 리뷰는 A 상품의 id 로 작성됨)

따라서 상품 id 를 기준으로, 올바르지 않게 매핑되어 있는 상품명-옵션명 정보를 수정하여 보정하는 역할을 담당함
(이때 상품 id 는 플랫폼의 상품 id 가 아닌 export 상품 id)

post processing 중 한 단계의 모듈 (Optional)

선행 데이터
- {export 플랫폼별 상품 id - 상품 정보} 매핑 데이터 (Required): export 플랫폼에 등록된 상품 id 와 상품 정보 매핑 데이터
"""


import logging
from typing import Union, Optional

import duckdb
import pandas as pd

from core.base.dataset.dataset_spec import DatasetSpec
from core.base.schema.attribute.base_product_option_mapping_attribute import \
    BaseProductOptionMappingAttributeSchema
from core.base.storage.base_storage import BaseStorage
from domain.platform.platform import Platform
from process.core.preprocess.preprocessing.preprocessor.resource.product_option_mapping_preprocessor import \
    export_product_id_to_product_option_mapping_preprocessing
from util.column_util import (
    validate_required_columns_in_df,
    drop_invalid_columns_data_safely,
    reindex_safely,
)
from util.excel_util import normalize_dataframe_types_strict
from util.logging_util import run_with_logging


@run_with_logging(
    lambda platform, **_: (
        {"platform": platform.get_platform_eng_name()}
        if platform is not None
        else {}
    )
)
def product_option_remapping(
        platform: Optional[Platform],
        df: pd.DataFrame,
        storage: BaseStorage,
        product_option_mapping_dataset_spec: DatasetSpec[BaseProductOptionMappingAttributeSchema],
        product_id_column: str,
        product_name_column: str,
        product_option_name_column: str,
) -> pd.DataFrame:
    """
    상품 id 정보를 기반으로 상품명/옵션명 정보 보정 및 반환

    외부 필수 및 참조 파일 BaseProductOptionMappingAttributeSchema 의 데이터를 기준으로
    상품명과 옵션명 데이터를 상품 id 에 맞춰 보정함

    주의 사항
    - 로직에 사용되는 필수 컬럼이 공백 혹은 None/NaN/Null 등 invalid 한 데이터일 경우, 해당 레코드는 제거됨

    보정 규칙
    - 보정 대상 df 와 상품 id 와 상품 정보 (상품명/옵션명) 가 매핑된 BaseProductOptionMappingAttributeSchema 외부 데이터와
      상품 id 를 기준으로 join (duck DB)
    - 기존 df 에 정의되어 있던 상품 정보를 외부 데이터 정보로 전부 덮어씀
    - 컬럼명은 기존 df 에 정의된 컬럼명으로 정의

    :param platform: 상품명/옵션명 정보 보정 대상 데이터의 플랫폼 정보 Optional[Platform]
    :param df: 보정 대상 pandas.DataFrame
    :param storage: 저장소 환경별 save/load 로직을 가진 BaseStorage
    :param product_option_mapping_dataset_spec: {리뷰 플랫폼 기준 상품 id - export 플랫폼별 상품 id} 정보 관련
                                                저장소 환경별 load 세부 설정과 컬럼명 정보 및 변환 컬럼명 정보를 가진 DatasetSpec
    :param product_id_column: 보정 대상 df 의 상품 id 관련 컬럼명 str
    :param product_name_column: 보정 대상 df 의 상품명 관련 컬럼명 str
    :param product_option_name_column: 보정 대상 df 의 옵션명 관련 컬럼명 str
    :return: 보정된 pandas.DataFrame
    """

    input_df_len = len(df)
    ordered_column_names = list(df.columns)

    df = df.copy()

    # {export 플랫폼별 상품 id - 상품 정보} 매핑 데이터 load 및 preprocessing
    # 데이터 추출 및 검증
    product_option_mapping_attribute_schema = product_option_mapping_dataset_spec.attribute_schema

    product_option_mapping_load_spec = product_option_mapping_dataset_spec.load_spec
    product_option_mapping_df = export_product_id_to_product_option_mapping_preprocessing(
        product_option_mapping_df=storage.load(product_option_mapping_dataset_spec.load_spec),
        source_attribute_schema=product_option_mapping_attribute_schema,
        file_path=product_option_mapping_load_spec.get_full_path(),
    )

    # duck db connect
    duckdb_connect = duckdb.connect()

    # 필수 컬럼 검증 및 duck db 등록
    # source (key) - target (value) 매핑
    required_source_target_column_mapping = {
        product_option_mapping_attribute_schema.EXPORT_PLATFORM_PRODUCT_ID: product_id_column,
        product_option_mapping_attribute_schema.PRODUCT_NAME: product_name_column,
        product_option_mapping_attribute_schema.PRODUCT_OPTION_NAME: product_option_name_column,
    }

    required_source_columns = list(required_source_target_column_mapping.keys())
    required_target_columns = list(required_source_target_column_mapping.values())

    # source
    validate_required_columns_in_df(
        df=product_option_mapping_df,
        column_names=required_source_columns,
    )

    drop_invalid_columns_data_safely(
        df=product_option_mapping_df,
        column_names=required_source_columns,
    )

    SOURCE_DF = "product_option_mapping_df"
    normalized_source_df = normalize_dataframe_types_strict(
        df=product_option_mapping_df,
        column_names=required_source_columns,
    )

    duckdb_connect.register(SOURCE_DF, normalized_source_df)

    # target
    validate_required_columns_in_df(
        df=df,
        column_names=required_target_columns,
    )

    drop_invalid_columns_data_safely(
        df=df,
        column_names=required_target_columns,
    )

    TARGET_DF = "target_df"
    normalized_target_df = normalize_dataframe_types_strict(
        df=df,
        column_names=required_target_columns,
    )

    duckdb_connect.register(TARGET_DF, normalized_target_df)

    # join & 보정
    select_query = ", ".join(
        [
            f"{SOURCE_DF}.{source_column} AS {target_column}"
            for source_column, target_column in required_source_target_column_mapping.items()
        ]
        + [
            f"{TARGET_DF}.{column}"
            for column in normalized_target_df.columns
            if column not in required_target_columns
        ]
    )

    from_query = f"""
        {SOURCE_DF}
        INNER JOIN {TARGET_DF}
        ON {SOURCE_DF}.{product_option_mapping_attribute_schema.EXPORT_PLATFORM_PRODUCT_ID}
        = {TARGET_DF}.{product_id_column}
    """

    remapping_query = \
        f"""
            SELECT
                {select_query}
            FROM
                {from_query}
        """

    joined_df = duckdb_connect.execute(remapping_query).df()

    join_keys = {product_option_mapping_attribute_schema.EXPORT_PLATFORM_PRODUCT_ID: product_id_column}
    logging.info(f"[MERGE] target_data=[{SOURCE_DF}, {TARGET_DF}], "
                 f"join_keys={join_keys}")

    duckdb_connect.close()

    # 필수 컬럼 dropna
    drop_invalid_columns_data_safely(
        df=joined_df,
        column_names=required_target_columns,
    )

    logging.info(f"[END] input_df_len={input_df_len}, processed_df_len={len(joined_df)}")

    joined_df = reindex_safely(
        df=joined_df,
        column_names=ordered_column_names,
        is_strict=True,
    )
    return joined_df
