"""
main.py
-------

preprocessing 의 실행부

개발 환경에서의 통합 테스트를 위한 수동 진입점 모듈이며,
하나의 대표 시나리오 조합 (environment: shopping mall - platform - export) 를
실제 데이터 기반으로 테스트 및 실행, 검증함
"""


from config.constant.common.name_constants import (
    REVIEW_SCRAPING_OUTPUT_XLSX_FILE_NAME,
    VREVIEW_TO_PLATFORM_PRODUCT_ID_MAPPING_XLSX_FILE_NAME,
    VREVIEW_TO_PLATFORM_PRODUCT_OPTION_MAPPING_XLSX_FILE_NAME,
    PREPROCESSING_OUTPUT_XLSX_FILE_NAME,
    ORDER_HISTORY_SCRAPING_OUTPUT_XLSX_FILE_NAME,
    VREVIEW_DIRECTORY_NAME,
    ABLY_DIRECTORY_NAME,
)
from core.common.bootstrap import run_bootstrap
from factory.bootstrap.config.local import LOCAL_BOOTSTRAP_CONFIG
from factory.config.registry.local import build_local_ini_config_registry
from factory.path.local import build_local_shopping_mall_platform_data_directory_path
from factory.pipeline.spec.local import LOCAL_PERIOD_DIRECTORY_NAME_DELIMITER
from factory.process.scraping.review_scraping_builder import build_ably_review_scraping_config
from core.base.dataset.dataset_spec import DatasetSpec
from domain.export.vreview.config.export_config import VReviewExportConfig
from domain.platform.ably.schema.id_mapping_attribute_schema import AblyVReviewProductIdMappingAttributeSchema
from domain.platform.ably.schema.order_history_scraping_attribute_schema import (
    AblyOrderHistoryScrapingReviewAttributeSchema
)
from domain.platform.ably.schema.review_scraping_attribute_schema import AblyReviewScrapingReviewAttributeSchema
from domain.platform.platform import Platform
from domain.export.vreview.schema.reference.product_option_mapping_attribute_schema import (
    VReviewProductOptionMappingAttributeSchema
)
from core.implementation.storage.excel.spec.excel_load_spec import ExcelLoadSpec
from core.implementation.storage.excel.spec.excel_save_spec import ExcelSaveSpec
from core.implementation.storage.excel.storage.excel_storage import ExcelStorage
from process.core.preprocess.preprocessing.preprocessing import preprocessing
from util.path_util import get_or_create_date_period_directory


def main():
    # environment (local) setting
    run_bootstrap(LOCAL_BOOTSTRAP_CONFIG)
    local_config_registry = build_local_ini_config_registry()
    excel_storage = ExcelStorage()

    # target export (vreview) setting
    vreview_export_config = VReviewExportConfig()

    vreview_product_option_mapping_load_spec = ExcelLoadSpec(
        root_path=build_local_shopping_mall_platform_data_directory_path(
            config_registry=local_config_registry,
            platform_name=VREVIEW_DIRECTORY_NAME,
        ),
        resource_name=VREVIEW_TO_PLATFORM_PRODUCT_OPTION_MAPPING_XLSX_FILE_NAME,
    )

    # source platform (ably) setting
    ably_review_scraping_config = build_ably_review_scraping_config(local_config_registry)

    ably_data_directory_path = build_local_shopping_mall_platform_data_directory_path(
        config_registry=local_config_registry,
        platform_name=ABLY_DIRECTORY_NAME,
    )
    ably_date_output_directory_path = get_or_create_date_period_directory(
        start_date=ably_review_scraping_config.get_scraping_start_date(),
        end_date=ably_review_scraping_config.get_scraping_end_date(),
        delimiter=LOCAL_PERIOD_DIRECTORY_NAME_DELIMITER,
        base_path=ably_data_directory_path,
    )

    ably_review_load_spec = ExcelLoadSpec(
        root_path=ably_date_output_directory_path,
        resource_name=REVIEW_SCRAPING_OUTPUT_XLSX_FILE_NAME,
    )

    ably_order_history_load_spec = ExcelLoadSpec(
        root_path=ably_data_directory_path,
        resource_name=ORDER_HISTORY_SCRAPING_OUTPUT_XLSX_FILE_NAME,
    )

    ably_vreview_product_id_mapping_load_spec = ExcelLoadSpec(
        root_path=ably_data_directory_path,
        resource_name=VREVIEW_TO_PLATFORM_PRODUCT_ID_MAPPING_XLSX_FILE_NAME,
    )

    ably_save_spec = ExcelSaveSpec(
        root_path=ably_date_output_directory_path,
        resource_name=PREPROCESSING_OUTPUT_XLSX_FILE_NAME,
        overwrite=True,
        pk_column_name=ably_review_scraping_config.get_mapped_pk_attribute_name(),
        sheet_name='review'
    )

    # execution
    preprocessing(
        platform=Platform.ABLY,
        export_config=vreview_export_config,
        storage=excel_storage,
        save_spec=ably_save_spec,
        product_id_mapping_dataset_spec=DatasetSpec(
            AblyVReviewProductIdMappingAttributeSchema,
            ably_vreview_product_id_mapping_load_spec,
        ),
        product_option_mapping_dataset_spec=DatasetSpec(
            VReviewProductOptionMappingAttributeSchema,
            vreview_product_option_mapping_load_spec,
        ),
        review_dataset_spec=DatasetSpec(
            AblyReviewScrapingReviewAttributeSchema,
            ably_review_load_spec,
        ),
        order_history_dataset_spec=DatasetSpec(
            AblyOrderHistoryScrapingReviewAttributeSchema,
            ably_order_history_load_spec,
        ),
    )


if __name__ == "__main__":
    main()
