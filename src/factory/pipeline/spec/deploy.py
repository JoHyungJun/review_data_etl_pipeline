"""
deploy.py
---------

배포 환경용 검증 및 XXXProcessPipelineSpec 인스턴스의 빌더 모듈
"""


from pathlib import Path

from config.constant.common.name_constants import (
    REVIEW_SCRAPING_OUTPUT_PARQUET_FILE_NAME,
    ORDER_HISTORY_SCRAPING_OUTPUT_PARQUET_FILE_NAME,
    PREPROCESSING_OUTPUT_PARQUET_FILE_NAME,
    POSTPROCESSING_OUTPUT_PARQUET_FILE_NAME,
    FINALIZING_SUCCESS_OUTPUT_PARQUET_FILE_NAME,
    FINALIZING_FAILED_OUTPUT_PARQUET_FILE_NAME,
    VREVIEW_TO_PLATFORM_PRODUCT_ID_MAPPING_PARQUET_FILE_NAME,
    VREVIEW_TO_PLATFORM_PRODUCT_OPTION_MAPPING_PARQUET_FILE_NAME,
    ABLY_DIRECTORY_NAME,
    VREVIEW_DIRECTORY_NAME,
    COUPANG_DIRECTORY_NAME,
)
from core.config.constant.schema_constants import COMMON
from core.config.model.config_registry import ConfigRegistry
from core.implementation.storage.s3.spec.s3_load_spec import S3LoadSpec
from core.implementation.storage.s3.spec.s3_save_spec import S3SaveSpec
from core.implementation.storage.s3.storage.s3_storage import S3Storage
from domain.export.vreview.config.export_config import VReviewExportConfig
from domain.export.vreview.schema.export.export_attribute_schema import VReviewExportAttributeSchema
from domain.export.vreview.schema.reference.product_option_mapping_attribute_schema import \
    VReviewProductOptionMappingAttributeSchema
from domain.platform.ably.pipeline.model.ably_process_pipeline_spec import AblyProcessPipelineSpec
from domain.platform.ably.schema.id_mapping_attribute_schema import AblyVReviewProductIdMappingAttributeSchema
from domain.platform.coupang.pipeline.model.coupang_process_pipeline_spec import CoupangProcessPipelineSpec
from domain.platform.coupang.schema.id_mapping_attribute_schema import CoupangVReviewProductIdMappingAttributeSchema
from factory.path.deploy import build_deploy_shopping_mall_platform_data_directory_path
from factory.process.scraping.order_history_scraping_builder import build_ably_order_history_scraping_config
from factory.process.scraping.review_scraping_builder import (
    build_ably_review_scraping_config,
    build_coupang_review_scraping_config,
)
from util.path_util import get_period_directory_name
from util.runtime_environment_util import resolve_value_from_environment_variables


# S3 용 환경변수 key
S3_BUCKET_NAME_ENVIRONMENT_KEY = "S3_BUCKET_NAME"
S3_ROOT_PATH_ENVIRONMENT_KEY = "S3_ROOT_PATH"

# 배포 환경용 기간별 디렉토리명 공통 구분자 상수
DEPLOY_PERIOD_DIRECTORY_NAME_DELIMITER = "_"


def build_deploy_ably_to_vreview_process_pipeline_spec(config_registry: ConfigRegistry) -> AblyProcessPipelineSpec:
    """
    배포 환경용 AblyProcessPipelineSpec 인스턴스의 빌더 메서드

    주의 사항
    - 현재 해당 메서드는 내부 규칙에 의해 실행 방식이 선택 및 실행되며,
      이후 추가적인 기능 확장 시 해당 메서드의 수정 혹은 메서드 추가가 요구됨

    내부 규칙
    - BaseStorage, Save/Load Spec 은 S3 를 기준
    - export 는 VReview 를 기준
    - 디렉토리/파일 명은 수집 날짜 기반 특정 포맷을 기준
    - 레퍼런스 외부 파일 경로는 프로젝트 구조 규칙을 기준

    :param config_registry: 설정값이 담긴 인스턴스 ConfigRegistry
    :return: 내부 규칙이 적용된 AblyProcessPipelineSpec
    """

    # 내부 규칙
    # storage
    storage = S3Storage()

    # export
    export_config = VReviewExportConfig()
    export_attribute_schema = VReviewExportAttributeSchema

    product_id_mapping_attribute_schema = AblyVReviewProductIdMappingAttributeSchema
    product_id_mapping_resource_name = VREVIEW_TO_PLATFORM_PRODUCT_ID_MAPPING_PARQUET_FILE_NAME

    product_option_mapping_attribute_schema = VReviewProductOptionMappingAttributeSchema
    product_option_mapping_resource_name = VREVIEW_TO_PLATFORM_PRODUCT_OPTION_MAPPING_PARQUET_FILE_NAME

    # platform
    review_scraping_config = build_ably_review_scraping_config(config_registry)
    order_history_scraping_config = build_ably_order_history_scraping_config(config_registry)

    # output format (name, path)
    bucket_name = resolve_value_from_environment_variables(S3_BUCKET_NAME_ENVIRONMENT_KEY)
    root_path = resolve_value_from_environment_variables(S3_ROOT_PATH_ENVIRONMENT_KEY)

    export_base_directory_path = build_deploy_shopping_mall_platform_data_directory_path(
        root_path=root_path,
        config_registry=config_registry,
        platform_name=VREVIEW_DIRECTORY_NAME,
    )

    platform_root_path = build_deploy_shopping_mall_platform_data_directory_path(
        root_path=root_path,
        config_registry=config_registry,
        platform_name=ABLY_DIRECTORY_NAME,
    )
    platform_output_base_path = Path(
        Path(platform_root_path)
        / get_period_directory_name(
            start_date=review_scraping_config.get_scraping_start_date(),
            end_date=review_scraping_config.get_scraping_end_date(),
            delimiter=DEPLOY_PERIOD_DIRECTORY_NAME_DELIMITER,
        )
    ).as_posix()

    # resource names
    review_scraping_output_resource_name = REVIEW_SCRAPING_OUTPUT_PARQUET_FILE_NAME
    order_history_scraping_output_resource_name = ORDER_HISTORY_SCRAPING_OUTPUT_PARQUET_FILE_NAME
    preprocessing_output_resource_name = PREPROCESSING_OUTPUT_PARQUET_FILE_NAME
    postprocessing_output_resource_name = POSTPROCESSING_OUTPUT_PARQUET_FILE_NAME
    finalizing_success_output_resource_name = FINALIZING_SUCCESS_OUTPUT_PARQUET_FILE_NAME
    finalizing_failed_output_resource_name = FINALIZING_FAILED_OUTPUT_PARQUET_FILE_NAME

    # spec
    review_scraping_load_spec = S3LoadSpec(
        root_path=platform_output_base_path,
        resource_name=review_scraping_output_resource_name,
        bucket_name=bucket_name,
    )

    order_history_scraping_load_spec = S3LoadSpec(
        root_path=platform_root_path,
        resource_name=order_history_scraping_output_resource_name,
        bucket_name=bucket_name,
    )

    return AblyProcessPipelineSpec(
        shopping_mall_name=config_registry.get_value(
            section_key=COMMON.SECTION_KEY,
            option_name=COMMON.SHOPPING_MALL_NAME,
        ),
        config_registry=config_registry,

        storage=storage,
        export_config=export_config,
        product_id_mapping_attribute_schema=product_id_mapping_attribute_schema,
        product_option_mapping_attribute_schema=product_option_mapping_attribute_schema,

        review_scraping_config=review_scraping_config,
        review_scraping_save_spec=S3SaveSpec(
            root_path=platform_output_base_path,
            resource_name=review_scraping_output_resource_name,
            overwrite=False,
            pk_key_name=review_scraping_config.get_mapped_pk_attribute_name(),
            bucket_name=bucket_name,
        ),
        review_scraping_load_spec=review_scraping_load_spec,

        order_history_scraping_config=order_history_scraping_config,
        order_history_scraping_save_spec=S3SaveSpec(
            root_path=platform_root_path,
            resource_name=order_history_scraping_output_resource_name,
            overwrite=False,
            pk_key_name=order_history_scraping_config.get_mapped_pk_attribute_name(),
            bucket_name=bucket_name,
        ),
        order_history_scraping_load_spec=order_history_scraping_load_spec,

        preprocessing_save_spec=S3SaveSpec(
            root_path=platform_output_base_path,
            resource_name=preprocessing_output_resource_name,
            overwrite=False,
            pk_key_name=review_scraping_config.get_mapped_pk_attribute_name(),
            bucket_name=bucket_name,
        ),
        preprocessing_load_spec=S3LoadSpec(
            root_path=platform_output_base_path,
            resource_name=preprocessing_output_resource_name,
            bucket_name=bucket_name,
        ),
        preprocessing_review_scraping_load_spec=review_scraping_load_spec,
        preprocessing_order_history_scraping_load_spec=order_history_scraping_load_spec,
        preprocessing_product_id_mapping_load_spec=S3LoadSpec(
            root_path=platform_root_path,
            resource_name=product_id_mapping_resource_name,
            bucket_name=bucket_name,
        ),
        preprocessing_product_option_mapping_load_spec=S3LoadSpec(
            root_path=export_base_directory_path,
            resource_name=product_option_mapping_resource_name,
            bucket_name=bucket_name,
        ),

        postprocessing_save_spec=S3SaveSpec(
            root_path=platform_output_base_path,
            resource_name=postprocessing_output_resource_name,
            overwrite=False,
            pk_key_name=export_attribute_schema.REVIEW_ID,
            bucket_name=bucket_name,
        ),
        postprocessing_load_spec=S3LoadSpec(
            root_path=platform_output_base_path,
            resource_name=postprocessing_output_resource_name,
            bucket_name=bucket_name,
        ),
        postprocessing_product_id_column_name=export_attribute_schema.PRODUCT_ID,
        postprocessing_product_option_name_column_name=export_attribute_schema.PRODUCT_OPTION_NAME,
        postprocessing_product_option_value_column_name=export_attribute_schema.PRODUCT_OPTION_VALUE,
        postprocessing_review_id_column_name=export_attribute_schema.REVIEW_ID,
        postprocessing_review_created_date_column_name=export_attribute_schema.REVIEW_CREATED_DATE,
        postprocessing_review_created_time_column_name=export_attribute_schema.REVIEW_CREATED_TIME,
        postprocessing_review_contents_column_name=export_attribute_schema.REVIEW_CONTENTS,

        finalizing_success_save_spec=S3SaveSpec(
            root_path=platform_output_base_path,
            resource_name=finalizing_success_output_resource_name,
            overwrite=False,
            pk_key_name=export_attribute_schema.REVIEW_ID,
            bucket_name=bucket_name,
        ),
        finalizing_failed_save_spec=S3SaveSpec(
            root_path=platform_output_base_path,
            resource_name=finalizing_failed_output_resource_name,
            overwrite=False,
            pk_key_name=export_attribute_schema.REVIEW_ID,
            bucket_name=bucket_name,
        ),
    )


def build_deploy_coupang_to_vreview_process_pipeline_spec(
    config_registry: ConfigRegistry,
) -> CoupangProcessPipelineSpec:
    """
    배포 환경용 CoupangProcessPipelineSpec 인스턴스의 빌더 메서드

    주의 사항
    - 현재 해당 메서드는 내부 규칙에 의해 실행 방식이 선택 및 실행되며,
      이후 추가적인 기능 확장 시 해당 메서드의 수정 혹은 메서드 추가가 요구됨

    내부 규칙
    - BaseStorage, Save/Load Spec 은 S3 를 기준
    - export 는 VReview 를 기준
    - 디렉토리/파일 명은 수집 날짜 기반 특정 포맷을 기준
    - 레퍼런스 외부 파일 경로는 프로젝트 구조 규칙을 기준

    :param config_registry: 설정값이 담긴 인스턴스 ConfigRegistry
    :return: 내부 규칙이 적용된 CoupangProcessPipelineSpec
    """

    # 내부 규칙

    # storage
    storage = S3Storage()

    # export
    export_config = VReviewExportConfig()
    export_attribute_schema = VReviewExportAttributeSchema

    product_id_mapping_attribute_schema = CoupangVReviewProductIdMappingAttributeSchema
    product_id_mapping_resource_name = VREVIEW_TO_PLATFORM_PRODUCT_ID_MAPPING_PARQUET_FILE_NAME

    product_option_mapping_attribute_schema = VReviewProductOptionMappingAttributeSchema
    product_option_mapping_resource_name = VREVIEW_TO_PLATFORM_PRODUCT_OPTION_MAPPING_PARQUET_FILE_NAME

    # platform
    review_scraping_config = build_coupang_review_scraping_config(config_registry)

    # output format (name, path)
    bucket_name = resolve_value_from_environment_variables(S3_BUCKET_NAME_ENVIRONMENT_KEY)
    root_path = resolve_value_from_environment_variables(S3_ROOT_PATH_ENVIRONMENT_KEY)

    export_base_directory_path = build_deploy_shopping_mall_platform_data_directory_path(
        root_path=root_path,
        config_registry=config_registry,
        platform_name=VREVIEW_DIRECTORY_NAME,
    )

    platform_root_path = build_deploy_shopping_mall_platform_data_directory_path(
        root_path=root_path,
        config_registry=config_registry,
        platform_name=COUPANG_DIRECTORY_NAME,
    )
    platform_output_base_path = Path(
        Path(platform_root_path)
        / get_period_directory_name(
            start_date=review_scraping_config.get_scraping_start_date(),
            end_date=review_scraping_config.get_scraping_end_date(),
            delimiter=DEPLOY_PERIOD_DIRECTORY_NAME_DELIMITER,
        )
    ).as_posix()

    # resource names
    review_scraping_output_resource_name = REVIEW_SCRAPING_OUTPUT_PARQUET_FILE_NAME
    preprocessing_output_resource_name = PREPROCESSING_OUTPUT_PARQUET_FILE_NAME
    postprocessing_output_resource_name = POSTPROCESSING_OUTPUT_PARQUET_FILE_NAME
    finalizing_success_output_resource_name = FINALIZING_SUCCESS_OUTPUT_PARQUET_FILE_NAME
    finalizing_failed_output_resource_name = FINALIZING_FAILED_OUTPUT_PARQUET_FILE_NAME

    # spec
    review_scraping_load_spec = S3LoadSpec(
        root_path=platform_output_base_path,
        resource_name=review_scraping_output_resource_name,
        bucket_name=bucket_name,
    )

    return CoupangProcessPipelineSpec(
        shopping_mall_name=config_registry.get_value(
            section_key=COMMON.SECTION_KEY,
            option_name=COMMON.SHOPPING_MALL_NAME,
        ),
        config_registry=config_registry,

        storage=storage,
        export_config=export_config,
        product_id_mapping_attribute_schema=product_id_mapping_attribute_schema,
        product_option_mapping_attribute_schema=product_option_mapping_attribute_schema,

        review_scraping_config=review_scraping_config,
        review_scraping_save_spec=S3SaveSpec(
            root_path=platform_output_base_path,
            resource_name=review_scraping_output_resource_name,
            overwrite=False,
            pk_key_name=review_scraping_config.get_mapped_pk_attribute_name(),
            bucket_name=bucket_name,
        ),
        review_scraping_load_spec=review_scraping_load_spec,

        preprocessing_save_spec=S3SaveSpec(
            root_path=platform_output_base_path,
            resource_name=preprocessing_output_resource_name,
            overwrite=False,
            pk_key_name=review_scraping_config.get_mapped_pk_attribute_name(),
            bucket_name=bucket_name,
        ),
        preprocessing_load_spec=S3LoadSpec(
            root_path=platform_output_base_path,
            resource_name=preprocessing_output_resource_name,
            bucket_name=bucket_name,
        ),
        preprocessing_review_scraping_load_spec=review_scraping_load_spec,
        preprocessing_product_id_mapping_load_spec=S3LoadSpec(
            root_path=platform_root_path,
            resource_name=product_id_mapping_resource_name,
            bucket_name=bucket_name,
        ),
        preprocessing_product_option_mapping_load_spec=S3LoadSpec(
            root_path=export_base_directory_path,
            resource_name=product_option_mapping_resource_name,
            bucket_name=bucket_name,
        ),

        postprocessing_save_spec=S3SaveSpec(
            root_path=platform_output_base_path,
            resource_name=postprocessing_output_resource_name,
            overwrite=False,
            pk_key_name=export_attribute_schema.REVIEW_ID,
            bucket_name=bucket_name,
        ),
        postprocessing_load_spec=S3LoadSpec(
            root_path=platform_output_base_path,
            resource_name=postprocessing_output_resource_name,
            bucket_name=bucket_name,
        ),
        postprocessing_product_id_column_name=export_attribute_schema.PRODUCT_ID,
        postprocessing_product_option_name_column_name=export_attribute_schema.PRODUCT_OPTION_NAME,
        postprocessing_product_option_value_column_name=export_attribute_schema.PRODUCT_OPTION_VALUE,
        postprocessing_review_id_column_name=export_attribute_schema.REVIEW_ID,
        postprocessing_review_created_date_column_name=export_attribute_schema.REVIEW_CREATED_DATE,
        postprocessing_review_created_time_column_name=export_attribute_schema.REVIEW_CREATED_TIME,
        postprocessing_review_contents_column_name=export_attribute_schema.REVIEW_CONTENTS,

        finalizing_success_save_spec=S3SaveSpec(
            root_path=platform_output_base_path,
            resource_name=finalizing_success_output_resource_name,
            overwrite=False,
            pk_key_name=export_attribute_schema.REVIEW_ID,
            bucket_name=bucket_name,
        ),
        finalizing_failed_save_spec=S3SaveSpec(
            root_path=platform_output_base_path,
            resource_name=finalizing_failed_output_resource_name,
            overwrite=False,
            pk_key_name=export_attribute_schema.REVIEW_ID,
            bucket_name=bucket_name,
        ),
    )
