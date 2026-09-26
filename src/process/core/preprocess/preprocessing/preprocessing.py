"""
preprocessing.py
----------------

플랫폼별 API 의 response 구조에 따른 데이터 전처리 및 구조 formatting 모듈

선행 데이터
- 리뷰 데이터 (Required): review_scraping.py 모듈을 통해 수집 및 formatting 된 리뷰 데이터
- 주문 내역 데이터 (Optional): order_history_scraping.py 를 통해 수집 및 formatting 된 주문 내역 데이터
- {리뷰 플랫폼 기준 상품 id - export 플랫폼별 상품 id} 매핑 데이터 (Required): 리뷰 플랫폼 기준 상품 id 와 export 플랫폼에 등록된 상품 id 매핑 데이터
- {export 플랫폼별 상품 id - 상품 정보} 매핑 데이터 (Required): export 플랫폼에 등록된 상품 id 와 상품 정보 매핑 데이터


주요 메서드
- preprocessing: 전체 프로세스 실행 중심부
"""


import logging
from typing import Optional

import duckdb

from factory.query.duckdb_builder import DuckDBQueryBuilder
from core.base.domain.export.base_export_config import BaseExportConfig
from core.base.dataset.dataset_spec import DatasetSpec
from core.base.schema.attribute.base_product_id_mapping_attribute_schema \
    import BaseProductIdMappingAttributeSchema
from core.base.schema.attribute.base_product_option_mapping_attribute \
    import BaseProductOptionMappingAttributeSchema
from core.base.schema.attribute.base_order_history_attribute_schema \
    import BaseOrderHistoryAttributeSchema
from core.base.schema.attribute.base_review_attribute_schema \
    import BaseReviewAttributeSchema
from core.base.schema.attribute.validation.attribute_schema_validate import (
    validate_datetime_fields,
    validate_order_id_dependency,
)
from core.base.storage.base_storage import BaseStorage
from core.base.storage.spec.base_save_spec import BaseStorageSaveSpec
from domain.platform.platform import Platform
from process.core.preprocess.preprocessing.model.context.source_data_context import SourceDataContext
from process.core.preprocess.preprocessing.preprocessor.resource.order_history_preprocessor import \
    order_history_preprocessing
from process.core.preprocess.preprocessing.preprocessor.resource.product_id_mapping_preprocessor import \
    platform_to_export_product_id_mapping_preprocessing
from process.core.preprocess.preprocessing.preprocessor.resource.product_option_mapping_preprocessor import \
    export_product_id_to_product_option_mapping_preprocessing
from process.core.preprocess.preprocessing.preprocessor.resource.review_preprocessor import review_preprocessing
from util.column_util import (
    rename_safely, reindex_safely, validate_required_columns_in_df,
)
from core.base.schema.attribute.util.attribute_schema_util import (
    build_prefixed_df_and_attribute_schema,
    build_prefixed_value,
    build_contains_flatten_mapping_by_priority, build_prefixed_attribute_schema,
    build_rename_mapping_by_constants_flatten_mapping,
)
from util.excel_util import normalize_dataframe_types_strict
from util.logging_util import run_with_logging, logging_file_event


@run_with_logging(
    lambda *args, **kwargs: (
        {"platform": kwargs["platform"].get_platform_eng_name()}
        if kwargs.get("platform") is not None
        else {}
    )
)
def preprocessing(
        platform: Platform,
        export_config: BaseExportConfig,
        storage: BaseStorage,
        save_spec: BaseStorageSaveSpec,
        product_id_mapping_dataset_spec: DatasetSpec[BaseProductIdMappingAttributeSchema],
        product_option_mapping_dataset_spec: DatasetSpec[BaseProductOptionMappingAttributeSchema],
        review_dataset_spec: DatasetSpec[BaseReviewAttributeSchema],
        order_history_dataset_spec: Optional[DatasetSpec[BaseOrderHistoryAttributeSchema]] = None,
) -> None:
    """
    수집된 데이터들에 대해 종합, formatting 및 저장 관련 중심부

    동작 방식
    - 이전 단계의 산출물들 및 설정 관련 데이터 load 및 merge (join)
    - 중요 컬럼 추출 및 formatting
    - export 별 formatting
    - storage, save_spec 기반 저장

    주의 사항
    - export attribute 의 경우 최종 산출물 정보를 관리하는 BaseExportConfig 에서 추출
    - 일관성 있는 컬럼명으로의 전처리를 위해, 모든 개별 데이터 (df) 의 preprocessing 은 PreprocessingAttributeSchema 기준으로 컬럼명을 변경 (rename) 하고,
      이후 PreprocessingAttributeSchema 의 상수로 개별 컬럼에 접근하여 진행
      (단, PreprocessingAttributeSchema 에 선언되지 않은 상수의 경우는 기존 XXXAttributeSchema 상수를 통해 접근해야 하며,
       merge 혹은 join 의 경우 개별 데이터의 preprocessing 진행 이후엔 PreprocessingAttributeSchema 상수로 진행해야 함)

    :param platform: 전처리 대상 데이터의 플랫폼 정보 Platform
    :param export_config: 최종 산출물 포맷 정보를 가진 BaseExportConfig
    :param storage: 저장소 환경별 save/load 로직을 가진 BaseStorage
    :param save_spec: 저장소 환경별 save 관련 세부 설정값을 가진 BaseStorageSaveSpec
    :param product_id_mapping_dataset_spec: {리뷰 플랫폼 기준 상품 id - export 플랫폼별 상품 id} 정보 관련
                                            저장소 환경별 load 세부 설정과 컬럼명 정보 및 변환 컬럼명 정보를 가진 DatasetSpec
    :param product_option_mapping_dataset_spec: {export 플랫폼별 상품 id - 상품 정보} 정보 관련
                                                저장소 환경별 load 세부 설정과 컬럼명 정보를 가진 DatasetSpec
    :param review_dataset_spec: 리뷰 데이터 관련 저장소 환경별 load 세부 설정과 컬럼명 정보 및 변환 컬럼명 정보를 가진 DatasetSpec
    :param order_history_dataset_spec: 주문 내역 데이터 관련 저장소 환경별 load 세부 설정과 컬럼명 정보 및 변환 컬럼명 정보를 가진 DatasetSpec (Optional)
    :return: 없음
    """

    # preprocessing 내부에서 사용할 공통 상수 선언
    REVIEW = "review"
    ORDER_HISTORY = "order_history"
    PRODUCT_ID_MAPPING = "id_mapping"
    PRODUCT_OPTION_MAPPING = "product_option_mapping"

    DELIMITER_FOR_ATTRIBUTE_SCHEMA = "__"

    # 리뷰 데이터 load 및 preprocessing
    # 데이터 추출 및 검증
    review_attribute_schema = review_dataset_spec.attribute_schema
    validate_datetime_fields(review_attribute_schema)

    review_load_spec = review_dataset_spec.load_spec
    review_df = storage.load(review_load_spec)

    validate_required_columns_in_df(
        df=review_df,
        column_names=review_attribute_schema.get_flatten_constants_name_value_mapping().values(),
    )

    # 전처리 로직을 위한 임시 prefixed rename df 및 prefixed attribute schema 추출
    prefixed_review_df, prefixed_review_attribute_schema \
        = build_prefixed_df_and_attribute_schema(
            df=review_df,
            source_schema=review_attribute_schema,
            full_prefix=build_prefixed_value(prefix=REVIEW, delimiter=DELIMITER_FOR_ATTRIBUTE_SCHEMA)
        )

    # 데이터 전처리
    preprocessed_review_attribute_schema = prefixed_review_attribute_schema

    preprocessed_review_df = review_preprocessing(
        review_df=prefixed_review_df,
        source_attribute_schema=prefixed_review_attribute_schema,
        file_path=review_load_spec.get_full_path(),
    )

    # 주문 내역 데이터 load 및 preprocessing
    preprocessed_order_history_attribute_schema = None
    preprocessed_order_history_df = None

    if order_history_dataset_spec is not None:
        # 데이터 추출 및 검증
        order_history_attribute_schema = order_history_dataset_spec.attribute_schema
        validate_order_id_dependency(review_attribute_schema, order_history_attribute_schema)

        order_history_load_spec = order_history_dataset_spec.load_spec
        order_history_df = storage.load(order_history_load_spec)

        validate_required_columns_in_df(
            df=order_history_df,
            column_names=order_history_attribute_schema.get_flatten_constants_name_value_mapping().values(),
        )

        # 전처리 로직을 위한 임시 prefixed rename df 및 prefixed attribute schema 추출
        prefixed_order_history_df, prefixed_order_history_attribute_schema \
            = build_prefixed_df_and_attribute_schema(
                df=order_history_df,
                source_schema=order_history_attribute_schema,
                full_prefix=build_prefixed_value(prefix=ORDER_HISTORY, delimiter=DELIMITER_FOR_ATTRIBUTE_SCHEMA)
            )

        # 데이터 전처리 및 이후의 전처리 과정을 위한 컬럼명 변경
        preprocessed_order_history_attribute_schema = prefixed_order_history_attribute_schema
        preprocessed_order_history_df = order_history_preprocessing(
            order_history_df=prefixed_order_history_df,
            source_attribute_schema=prefixed_order_history_attribute_schema,
            file_path=order_history_load_spec.get_full_path(),
        )

    # {리뷰 플랫폼 기준 상품 id - export 플랫폼별 상품 id} 매핑 데이터 load 및 preprocessing
    # 데이터 추출 및 검증
    product_id_mapping_attribute_schema = product_id_mapping_dataset_spec.attribute_schema

    product_id_mapping_load_spec = product_id_mapping_dataset_spec.load_spec

    # 경로 존재 여부 검증 (reference 파일이 반드시 존재해야 함)
    if not product_id_mapping_load_spec.get_full_path().exists():
        logging_file_event(
            file_path=product_id_mapping_load_spec.get_full_path(),
            log_prefix="LOAD",
            log_metadata={
                "platform": platform.get_platform_eng_name(),
                "process": "preprocessing",
                "target_reference_file": "product_id_mapping"
            },
            log_message="Invalid path - reference file is required for preprocessing",
            log_level="error",
        )
        raise FileNotFoundError(
            "리뷰 데이터 전처리 과정에선 "
            "{리뷰 플랫폼 기준 상품 id - export 플랫폼별 상품 id} 매핑 관련 레퍼런스 외부 파일이 필수로 요구됩니다. "
            "프로젝트 구조 혹은 요청 데이터를 확인해주세요."
        )

    product_id_mapping_df = storage.load(product_id_mapping_load_spec)

    validate_required_columns_in_df(
        df=product_id_mapping_df,
        column_names=product_id_mapping_attribute_schema.get_flatten_constants_name_value_mapping().values(),
    )

    # 전처리 로직을 위한 임시 prefixed rename df 및 prefixed attribute schema 추출
    prefixed_product_id_mapping_df, prefixed_product_id_mapping_attribute_schema \
        = build_prefixed_df_and_attribute_schema(
            df=product_id_mapping_df,
            source_schema=product_id_mapping_attribute_schema,
            full_prefix=build_prefixed_value(prefix=PRODUCT_ID_MAPPING, delimiter=DELIMITER_FOR_ATTRIBUTE_SCHEMA),
        )

    # 데이터 전처리 및 이후의 전처리 과정을 위한 컬럼명 변경
    preprocessed_product_id_mapping_attribute_schema = prefixed_product_id_mapping_attribute_schema
    preprocessed_product_id_mapping_df = platform_to_export_product_id_mapping_preprocessing(
        product_id_mapping_df=prefixed_product_id_mapping_df,
        source_attribute_schema=prefixed_product_id_mapping_attribute_schema,
        file_path=product_id_mapping_load_spec.get_full_path(),
    )

    # {export 플랫폼별 상품 id - 상품 정보} 매핑 데이터 load 및 preprocessing
    # 데이터 추출 및 검증
    product_option_mapping_attribute_schema = product_option_mapping_dataset_spec.attribute_schema

    product_option_mapping_load_spec = product_option_mapping_dataset_spec.load_spec
    if not product_option_mapping_load_spec.get_full_path().exists():
        logging_file_event(
            file_path=product_option_mapping_load_spec.get_full_path(),
            log_prefix="LOAD",
            log_metadata={
                "platform": platform.get_platform_eng_name(),
                "process": "preprocessing",
                "target_reference_file": "product_option_mapping"
            },
            log_message="Invalid path - reference file is required for preprocessing",
            log_level="error",
        )
        raise FileNotFoundError(
            "리뷰 데이터 전처리 과정에선 "
            "{export 플랫폼별 상품 id - 상품 정보} 매핑 관련 레퍼런스 외부 파일이 필수로 요구됩니다. "
            "프로젝트 구조 혹은 요청 데이터를 확인해주세요."
        )

    product_option_mapping_df = storage.load(product_option_mapping_load_spec)

    validate_required_columns_in_df(
        df=product_option_mapping_df,
        column_names=product_option_mapping_attribute_schema.get_flatten_constants_name_value_mapping().values(),
    )

    # 전처리 로직을 위한 임시 prefixed rename df 및 prefixed attribute schema 추출
    prefixed_product_option_mapping_df, prefixed_product_option_mapping_attribute_schema \
        = build_prefixed_df_and_attribute_schema(
            df=product_option_mapping_df,
            source_schema=product_option_mapping_attribute_schema,
            full_prefix=build_prefixed_value(prefix=PRODUCT_OPTION_MAPPING, delimiter=DELIMITER_FOR_ATTRIBUTE_SCHEMA)
        )

    # 데이터 전처리 및 이후의 전처리 과정을 위한 컬럼명 변경
    preprocessed_product_option_mapping_attribute_schema = prefixed_product_option_mapping_attribute_schema
    preprocessed_product_option_mapping_df = export_product_id_to_product_option_mapping_preprocessing(
        product_option_mapping_df=prefixed_product_option_mapping_df,
        source_attribute_schema=prefixed_product_option_mapping_attribute_schema,
        file_path=product_option_mapping_load_spec.get_full_path(),
    )

    # join
    with duckdb.connect() as duckdb_connect:

        # duck db 등록을 위해 컬럼 타입 단일화
        normalized_review_df = normalize_dataframe_types_strict(preprocessed_review_df)
        normalized_product_id_mapping_df = normalize_dataframe_types_strict(preprocessed_product_id_mapping_df)
        normalized_product_option_mapping_df = normalize_dataframe_types_strict(preprocessed_product_option_mapping_df)

        duckdb_connect.register(REVIEW, normalized_review_df)

        JOINED = "JOINED"
        DELIMITER_FOR_JOIN_VIEW = "_"

        JOINED = build_prefixed_value(JOINED, DELIMITER_FOR_JOIN_VIEW, REVIEW)

        # review df & order history df join (Optional)
        if preprocessed_order_history_df is not None:
            normalized_order_history_df = normalize_dataframe_types_strict(preprocessed_order_history_df)

            duckdb_connect.register(ORDER_HISTORY, normalized_order_history_df)

            review_order_history_join_keys = {
                preprocessed_review_attribute_schema.ORDER_ID:
                    preprocessed_order_history_attribute_schema.ORDER_ID
            }

            review_order_history_join_query = DuckDBQueryBuilder.build_simple_join_query(
                left_view_name=REVIEW,
                right_view_name=ORDER_HISTORY,
                join_keys=review_order_history_join_keys,
                how="LEFT"
            )

            JOINED = build_prefixed_value(JOINED, DELIMITER_FOR_JOIN_VIEW, ORDER_HISTORY)
            duckdb_connect.execute(
                DuckDBQueryBuilder.build_create_temp_view_query(
                    output_view_name=JOINED,
                    query=review_order_history_join_query,
                )
            )
            logging.info(f"[MERGE] target_data=[{REVIEW}, {ORDER_HISTORY}], "
                         f"join_keys={review_order_history_join_keys}")

        # joined df (or review df) & id mapping df join
        duckdb_connect.register(PRODUCT_ID_MAPPING, normalized_product_id_mapping_df)

        review_product_id_mapping_join_keys = {
            preprocessed_review_attribute_schema.PRODUCT_ID:
                preprocessed_product_id_mapping_attribute_schema.SCRAPING_PLATFORM_PRODUCT_ID
        }

        review_product_id_join_query = DuckDBQueryBuilder.build_simple_join_query(
            left_view_name=JOINED,
            right_view_name=PRODUCT_ID_MAPPING,
            join_keys=review_product_id_mapping_join_keys,
            how="LEFT"
        )

        JOINED = build_prefixed_value(JOINED, DELIMITER_FOR_JOIN_VIEW, PRODUCT_ID_MAPPING)
        duckdb_connect.execute(
            DuckDBQueryBuilder.build_create_temp_view_query(
                output_view_name=JOINED,
                query=review_product_id_join_query,
            )
        )
        logging.info(f"[MERGE] target_data=[{JOINED}, {PRODUCT_ID_MAPPING}], "
                     f"join_keys={review_product_id_mapping_join_keys}")

        # joined df & product option mapping df join
        duckdb_connect.register(PRODUCT_OPTION_MAPPING, normalized_product_option_mapping_df)

        export_id_product_option_mapping_join_keys = {
            preprocessed_product_id_mapping_attribute_schema.EXPORT_PLATFORM_PRODUCT_ID:
                preprocessed_product_option_mapping_attribute_schema.EXPORT_PLATFORM_PRODUCT_ID
        }

        export_id_product_option_mapping_join_query = DuckDBQueryBuilder.build_simple_join_query(
            left_view_name=JOINED,
            right_view_name=PRODUCT_OPTION_MAPPING,
            join_keys=export_id_product_option_mapping_join_keys,
            how="LEFT"
        )

        JOINED = build_prefixed_value(JOINED, DELIMITER_FOR_JOIN_VIEW, PRODUCT_OPTION_MAPPING)
        duckdb_connect.execute(
            DuckDBQueryBuilder.build_create_temp_view_query(
                output_view_name=JOINED,
                query=export_id_product_option_mapping_join_query,
            )
        )
        logging.info(f"[MERGE] target_data=[{JOINED}, {PRODUCT_OPTION_MAPPING}], "
                     f"join_keys={export_id_product_option_mapping_join_keys}")

        # duck db to data frame
        joined_df = duckdb_connect.execute(
            DuckDBQueryBuilder.build_select_all_query(JOINED)
        ).df()

    # export formatting
    export_attribute_schema = export_config.get_attribute_schema()
    EXPORT_PLATFORM_NAME = export_config.get_export_eng_name()

    preprocessed_vreview_export_schema = build_prefixed_attribute_schema(
        source_schema=export_attribute_schema,
        full_prefix=build_prefixed_value(prefix=EXPORT_PLATFORM_NAME, delimiter=DELIMITER_FOR_ATTRIBUTE_SCHEMA)
    )

    # default mapping schema
    # priority 에 따라 임시 default 로 선언된 컬럼 정보이며, 상세 수정은 export preprocessing 에서 구현 책임을 가짐
    contains_constants_flatten_mapping = build_contains_flatten_mapping_by_priority(
        prioritized_attribute_schemas=[
            preprocessed_review_attribute_schema,
            *(
                [preprocessed_order_history_attribute_schema]
                if preprocessed_order_history_attribute_schema is not None else []
            ),
            preprocessed_product_id_mapping_attribute_schema,
            preprocessed_product_option_mapping_attribute_schema,
        ],
        target_schema=preprocessed_vreview_export_schema,
    )

    # filtering & rename (이후의 로직은 export schema 를 기준으로 수행되어야 함)
    # filtering (컬럼 탈락)
    indexed_df = reindex_safely(
        df=joined_df,
        column_names=list(contains_constants_flatten_mapping.values()),
    )

    # rename (컬럼명 export format 기준으로 변경)
    rename_mapping = build_rename_mapping_by_constants_flatten_mapping(
        source_constants_flatten_mapping=contains_constants_flatten_mapping,
        target_constants_flatten_mapping=export_attribute_schema.get_flatten_constants_name_value_mapping(),
    )

    renamed_df = rename_safely(
        df=indexed_df,
        column_name_mapping=rename_mapping,
    )

    # export preprocessing
    source_data_context = SourceDataContext(
        joined_df=joined_df,
        product_id_mapping_attribute_schema=preprocessed_product_id_mapping_attribute_schema,
        product_option_mapping_attribute_schema=preprocessed_product_option_mapping_attribute_schema,
        review_attribute_schema=preprocessed_review_attribute_schema,
        order_history_attribute_schema=preprocessed_order_history_attribute_schema,
    )

    preprocessed_df = export_config.apply_export_preprocessing(
        target_platform=platform,
        export_formatted_df=renamed_df,
        source_data_context=source_data_context,
    )

    # reindex (최종 포맷으로 컬럼 순서 변경)
    final_df = reindex_safely(
        df=preprocessed_df,
        column_names=export_attribute_schema.get_ordered_flatten_constants_value(),
    )

    # 저장
    storage.save(
        save_spec=save_spec,
        df=final_df,
    )
    logging_file_event(file_path=save_spec.get_full_path(), log_prefix="SAVE")
