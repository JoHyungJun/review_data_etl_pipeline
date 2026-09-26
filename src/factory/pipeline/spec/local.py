"""
local.py
--------

로컬 환경용 검증 및 XXXProcessPipelineSpec 인스턴스의 빌더 모듈
"""


from config.constant.common.name_constants import (
    REVIEW_SCRAPING_OUTPUT_XLSX_FILE_NAME,
    ORDER_HISTORY_SCRAPING_OUTPUT_XLSX_FILE_NAME,
    PREPROCESSING_OUTPUT_XLSX_FILE_NAME,
    POSTPROCESSING_OUTPUT_XLSX_FILE_NAME,
    FINALIZING_SUCCESS_OUTPUT_XLSX_FILE_NAME,
    FINALIZING_FAILED_OUTPUT_XLSX_FILE_NAME,
    VREVIEW_ID_TO_PLATFORM_ID_MAPPING_XLSX_FILE_NAME,
    VREVIEW_ID_TO_PRODUCT_OPTION_MAPPING_XLSX_FILE_NAME, VREVIEW_DIRECTORY_NAME, ABLY_DIRECTORY_NAME,
    COUPANG_DIRECTORY_NAME,
)
from core.config.model.config_registry import ConfigRegistry
from core.implementation.storage.excel.spec.excel_load_spec import ExcelLoadSpec
from core.implementation.storage.excel.spec.excel_save_spec import ExcelSaveSpec
from core.implementation.storage.excel.storage.excel_storage import ExcelStorage
from domain.export.vreview.config.export_config import VReviewExportConfig
from domain.export.vreview.schema.export.export_attribute_schema import VReviewExportAttributeSchema
from domain.export.vreview.schema.reference.product_option_mapping_attribute_schema import (
    VReviewProductOptionMappingAttributeSchema
)
from domain.platform.ably.pipeline.model.ably_process_pipeline_spec import AblyProcessPipelineSpec
from domain.platform.ably.schema.id_mapping_attribute_schema import AblyVReviewProductIdMappingAttributeSchema
from domain.platform.coupang.pipeline.model.coupang_process_pipeline_spec import CoupangProcessPipelineSpec
from domain.platform.coupang.schema.id_mapping_attribute_schema import CoupangVReviewProductIdMappingAttributeSchema
from factory.path.local import build_local_shopping_mall_platform_data_directory_path
from factory.process.scraping.order_history_scraping_builder import build_ably_order_history_scraping_config
from factory.process.scraping.review_scraping_builder import (
    build_ably_review_scraping_config,
    build_coupang_review_scraping_config,
)
from util.path_util import get_or_create_date_period_directory


def build_local_ably_pipeline_spec(config_registry: ConfigRegistry) -> AblyProcessPipelineSpec:
    """
    로컬 환경용 AblyProcessPipelineSpec 인스턴스의 빌더 메서드

    주의 사항
    - 현재 해당 메서드는 내부 규칙에 의해 실행 방식이 선택 및 실행되며,
      이후 추가적인 기능 확장 시 해당 메서드의 수정 혹은 메서드 추가가 요구됨

    내부 규칙
    - BaseStorage, Save/Load Spec 은 Excel 을 기준
    - export 는 VReview 를 기준
    - 디렉토리/파일 명은 수집 날짜 기반 특정 포맷을 기준
    - 레퍼런스 외부 파일 경로는 프로젝트 구조 규칙을 기준

    :param config_registry: 설정값이 담긴 인스턴스 ConfigRegistry
    :return: 내부 규칙이 적용된 AblyProcessPipelineSpec
    """

    # 내부 규칙
    # storage
    storage = ExcelStorage()
    sheet_name = 'review'

    # export
    export_config = VReviewExportConfig()
    export_attribute_schema = VReviewExportAttributeSchema

    product_id_mapping_attribute_schema = AblyVReviewProductIdMappingAttributeSchema
    product_id_mapping_resource_name = VREVIEW_ID_TO_PLATFORM_ID_MAPPING_XLSX_FILE_NAME

    product_option_mapping_attribute_schema = VReviewProductOptionMappingAttributeSchema
    product_option_mapping_resource_name = VREVIEW_ID_TO_PRODUCT_OPTION_MAPPING_XLSX_FILE_NAME

    # platform
    review_scraping_config = build_ably_review_scraping_config(config_registry)
    order_history_scraping_config = build_ably_order_history_scraping_config(config_registry)

    # directory/file format (name, path)
    export_base_directory_path = build_local_shopping_mall_platform_data_directory_path(
        config_registry=config_registry,
        platform_name=VREVIEW_DIRECTORY_NAME,
    )

    platform_base_directory_path = build_local_shopping_mall_platform_data_directory_path(
        config_registry=config_registry,
        platform_name=ABLY_DIRECTORY_NAME,
    )
    platform_output_directory_path = get_or_create_date_period_directory(
        start_date=review_scraping_config.get_scraping_start_date(),
        end_date=review_scraping_config.get_scraping_end_date(),
        base_path=platform_base_directory_path,
    )

    review_scraping_output_resource_name = REVIEW_SCRAPING_OUTPUT_XLSX_FILE_NAME
    order_history_scraping_output_resource_name = ORDER_HISTORY_SCRAPING_OUTPUT_XLSX_FILE_NAME
    preprocessing_output_resource_name = PREPROCESSING_OUTPUT_XLSX_FILE_NAME
    postprocessing_output_resource_name = POSTPROCESSING_OUTPUT_XLSX_FILE_NAME
    finalizing_success_output_resource_name = FINALIZING_SUCCESS_OUTPUT_XLSX_FILE_NAME
    finalizing_failed_output_resource_name = FINALIZING_FAILED_OUTPUT_XLSX_FILE_NAME

    # spec
    review_scraping_load_spec = ExcelLoadSpec(
        root_path=platform_output_directory_path,
        resource_name=review_scraping_output_resource_name,
    )
    order_history_scraping_load_spec = ExcelLoadSpec(
        root_path=platform_base_directory_path,
        resource_name=order_history_scraping_output_resource_name,
    )

    return AblyProcessPipelineSpec(
        config_registry=config_registry,

        storage=storage,
        export_config=export_config,
        product_id_mapping_attribute_schema=product_id_mapping_attribute_schema,
        product_option_mapping_attribute_schema=product_option_mapping_attribute_schema,

        review_scraping_config=review_scraping_config,
        review_scraping_save_spec=ExcelSaveSpec(
            root_path=platform_output_directory_path,
            resource_name=review_scraping_output_resource_name,
            overwrite=False,
            pk_column_name=review_scraping_config.get_mapped_pk_attribute_name(),
            sheet_name=sheet_name,
        ),
        review_scraping_load_spec=review_scraping_load_spec,

        order_history_scraping_config=order_history_scraping_config,
        order_history_scraping_save_spec=ExcelSaveSpec(
            root_path=platform_base_directory_path,
            resource_name=order_history_scraping_output_resource_name,
            overwrite=False,
            pk_column_name=order_history_scraping_config.get_mapped_pk_attribute_name(),
            sheet_name=sheet_name,
        ),
        order_history_scraping_load_spec=order_history_scraping_load_spec,

        preprocessing_save_spec=ExcelSaveSpec(
            root_path=platform_output_directory_path,
            resource_name=preprocessing_output_resource_name,
            overwrite=False,
            pk_column_name=review_scraping_config.get_mapped_pk_attribute_name(),
            sheet_name=sheet_name,
        ),
        preprocessing_load_spec=ExcelLoadSpec(
            root_path=platform_output_directory_path,
            resource_name=preprocessing_output_resource_name,
        ),
        preprocessing_review_scraping_load_spec=review_scraping_load_spec,
        preprocessing_order_history_scraping_load_spec=order_history_scraping_load_spec,
        preprocessing_product_id_mapping_load_spec=ExcelLoadSpec(
            root_path=platform_base_directory_path,
            resource_name=product_id_mapping_resource_name,
        ),
        preprocessing_product_option_mapping_load_spec=ExcelLoadSpec(
            root_path=export_base_directory_path,
            resource_name=product_option_mapping_resource_name,
        ),

        postprocessing_save_spec=ExcelSaveSpec(
            root_path=platform_output_directory_path,
            resource_name=postprocessing_output_resource_name,
            overwrite=False,
            pk_column_name=export_attribute_schema.REVIEW_ID,
            sheet_name=sheet_name,
        ),
        postprocessing_load_spec=ExcelLoadSpec(
            root_path=platform_output_directory_path,
            resource_name=postprocessing_output_resource_name,
        ),
        postprocessing_product_id_column_name=export_attribute_schema.PRODUCT_ID,
        postprocessing_product_option_name_column_name=export_attribute_schema.PRODUCT_OPTION_NAME,
        postprocessing_product_option_value_column_name=export_attribute_schema.PRODUCT_OPTION_VALUE,
        postprocessing_review_id_column_name=export_attribute_schema.REVIEW_ID,
        postprocessing_review_created_date_column_name=export_attribute_schema.REVIEW_CREATED_DATE,
        postprocessing_review_created_time_column_name=export_attribute_schema.REVIEW_CREATED_TIME,
        postprocessing_review_contents_column_name=export_attribute_schema.REVIEW_CONTENTS,

        finalizing_success_save_spec=ExcelSaveSpec(
            root_path=platform_output_directory_path,
            resource_name=finalizing_success_output_resource_name,
            overwrite=False,
            pk_column_name=export_attribute_schema.REVIEW_ID,
            sheet_name=sheet_name,
        ),
        finalizing_failed_save_spec=ExcelSaveSpec(
            root_path=platform_output_directory_path,
            resource_name=finalizing_failed_output_resource_name,
            overwrite=False,
            pk_column_name=export_attribute_schema.REVIEW_ID,
            sheet_name=sheet_name,
        ),
    )


def build_local_coupang_pipeline_spec(config_registry: ConfigRegistry) -> CoupangProcessPipelineSpec:
    """
    로컬 환경용 CoupangProcessPipelineSpec 인스턴스의 빌더 메서드

    주의 사항
    - 현재 해당 메서드는 내부 규칙에 의해 실행 방식이 선택 및 실행되며,
      이후 추가적인 기능 확장 시 해당 메서드의 수정 혹은 메서드 추가가 요구됨

    내부 규칙
    - BaseStorage, Save/Load Spec 은 Excel 을 기준
    - export 는 VReview 를 기준
    - 디렉토리/파일 명은 수집 날짜 기반 특정 포맷을 기준
    - 레퍼런스 외부 파일 경로는 프로젝트 구조 규칙을 기준

    :param config_registry: 설정값이 담긴 인스턴스 ConfigRegistry
    :return: 내부 규칙이 적용된 CoupangProcessPipelineSpec
    """

    # 내부 규칙
    # storage
    storage = ExcelStorage()
    sheet_name = 'review'

    # export
    export_config = VReviewExportConfig()
    export_attribute_schema = VReviewExportAttributeSchema

    product_id_mapping_attribute_schema = CoupangVReviewProductIdMappingAttributeSchema
    product_id_mapping_resource_name = VREVIEW_ID_TO_PLATFORM_ID_MAPPING_XLSX_FILE_NAME

    product_option_mapping_attribute_schema = VReviewProductOptionMappingAttributeSchema
    product_option_mapping_resource_name = VREVIEW_ID_TO_PRODUCT_OPTION_MAPPING_XLSX_FILE_NAME

    # platform
    review_scraping_config = build_coupang_review_scraping_config(config_registry)

    # directory/file format (name, path)
    export_base_directory_path = build_local_shopping_mall_platform_data_directory_path(
        config_registry=config_registry,
        platform_name=VREVIEW_DIRECTORY_NAME,
    )

    platform_base_directory_path = build_local_shopping_mall_platform_data_directory_path(
        config_registry=config_registry,
        platform_name=COUPANG_DIRECTORY_NAME,
    )
    platform_output_directory_path = get_or_create_date_period_directory(
        start_date=review_scraping_config.get_scraping_start_date(),
        end_date=review_scraping_config.get_scraping_end_date(),
        base_path=platform_base_directory_path,
    )

    review_scraping_output_resource_name = REVIEW_SCRAPING_OUTPUT_XLSX_FILE_NAME
    preprocessing_output_resource_name = PREPROCESSING_OUTPUT_XLSX_FILE_NAME
    postprocessing_output_resource_name = POSTPROCESSING_OUTPUT_XLSX_FILE_NAME
    finalizing_success_output_resource_name = FINALIZING_SUCCESS_OUTPUT_XLSX_FILE_NAME
    finalizing_failed_output_resource_name = FINALIZING_FAILED_OUTPUT_XLSX_FILE_NAME

    # spec
    review_scraping_load_spec = ExcelLoadSpec(
        root_path=platform_output_directory_path,
        resource_name=review_scraping_output_resource_name,
    )

    return CoupangProcessPipelineSpec(
        config_registry=config_registry,

        storage=storage,
        export_config=export_config,
        product_id_mapping_attribute_schema=product_id_mapping_attribute_schema,
        product_option_mapping_attribute_schema=product_option_mapping_attribute_schema,

        review_scraping_config=review_scraping_config,
        review_scraping_save_spec=ExcelSaveSpec(
            root_path=platform_output_directory_path,
            resource_name=review_scraping_output_resource_name,
            overwrite=False,
            pk_column_name=review_scraping_config.get_mapped_pk_attribute_name(),
            sheet_name=sheet_name,
        ),
        review_scraping_load_spec=review_scraping_load_spec,

        preprocessing_save_spec=ExcelSaveSpec(
            root_path=platform_output_directory_path,
            resource_name=preprocessing_output_resource_name,
            overwrite=False,
            pk_column_name=review_scraping_config.get_mapped_pk_attribute_name(),
            sheet_name=sheet_name,
        ),
        preprocessing_load_spec=ExcelLoadSpec(
            root_path=platform_output_directory_path,
            resource_name=preprocessing_output_resource_name,
        ),
        preprocessing_review_scraping_load_spec=review_scraping_load_spec,
        preprocessing_product_id_mapping_load_spec=ExcelLoadSpec(
            root_path=platform_base_directory_path,
            resource_name=product_id_mapping_resource_name,
        ),
        preprocessing_product_option_mapping_load_spec=ExcelLoadSpec(
            root_path=export_base_directory_path,
            resource_name=product_option_mapping_resource_name,
        ),

        postprocessing_save_spec=ExcelSaveSpec(
            root_path=platform_output_directory_path,
            resource_name=postprocessing_output_resource_name,
            overwrite=False,
            pk_column_name=export_attribute_schema.REVIEW_ID,
            sheet_name=sheet_name,
        ),
        postprocessing_load_spec=ExcelLoadSpec(
            root_path=platform_output_directory_path,
            resource_name=postprocessing_output_resource_name,
        ),
        postprocessing_product_id_column_name=export_attribute_schema.PRODUCT_ID,
        postprocessing_product_option_name_column_name=export_attribute_schema.PRODUCT_OPTION_NAME,
        postprocessing_product_option_value_column_name=export_attribute_schema.PRODUCT_OPTION_VALUE,
        postprocessing_review_id_column_name=export_attribute_schema.REVIEW_ID,
        postprocessing_review_created_date_column_name=export_attribute_schema.REVIEW_CREATED_DATE,
        postprocessing_review_created_time_column_name=export_attribute_schema.REVIEW_CREATED_TIME,
        postprocessing_review_contents_column_name=export_attribute_schema.REVIEW_CONTENTS,

        finalizing_success_save_spec=ExcelSaveSpec(
            root_path=platform_output_directory_path,
            resource_name=finalizing_success_output_resource_name,
            overwrite=False,
            pk_column_name=export_attribute_schema.REVIEW_ID,
            sheet_name=sheet_name,
        ),
        finalizing_failed_save_spec=ExcelSaveSpec(
            root_path=platform_output_directory_path,
            resource_name=finalizing_failed_output_resource_name,
            overwrite=False,
            pk_column_name=export_attribute_schema.REVIEW_ID,
            sheet_name=sheet_name,
        ),
    )