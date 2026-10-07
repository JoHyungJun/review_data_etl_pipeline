"""
main.py
-------

finalizing 의 실행부

개발 환경에서의 통합 테스트를 위한 수동 진입점 모듈이며,
하나의 대표 시나리오 조합 (environment: shopping mall - platform - export) 를
실제 데이터 기반으로 테스트 및 실행, 검증함
"""


from config.constant.common.name_constants import (
    POSTPROCESSING_OUTPUT_XLSX_FILE_NAME,
    FINALIZING_SUCCESS_OUTPUT_XLSX_FILE_NAME,
    FINALIZING_FAILED_OUTPUT_XLSX_FILE_NAME,
    ABLY_DIRECTORY_NAME,
)
from core.common.bootstrap import run_bootstrap
from core.implementation.storage.excel.spec.excel_load_spec import ExcelLoadSpec
from core.implementation.storage.excel.spec.excel_save_spec import ExcelSaveSpec
from core.implementation.storage.excel.storage.excel_storage import ExcelStorage
from domain.export.vreview.config.export_config import VReviewExportConfig
from domain.export.vreview.schema.export.export_attribute_schema import VReviewExportAttributeSchema
from domain.platform.platform import Platform
from factory.bootstrap.config.local import LOCAL_BOOTSTRAP_CONFIG
from factory.config.registry.local import build_local_ini_config_registry
from factory.path.local import build_local_shopping_mall_platform_data_directory_path
from factory.pipeline.spec.local import LOCAL_PERIOD_DIRECTORY_NAME_DELIMITER
from factory.process.scraping.review_scraping_builder import build_ably_review_scraping_config
from process.core.finalize.finalizing.finalizing import finalizing
from util.path_util import get_or_create_date_period_directory


def main():
    # environment (local) setting
    run_bootstrap(LOCAL_BOOTSTRAP_CONFIG)
    local_config_registry = build_local_ini_config_registry()
    excel_storage = ExcelStorage()

    # target export (vreview) setting
    vreview_export_attribute_schema = VReviewExportAttributeSchema
    vreview_export_config = VReviewExportConfig()

    # source platform (ably) setting
    ably_review_scraping_config = build_ably_review_scraping_config(local_config_registry)

    ably_date_output_directory_path = get_or_create_date_period_directory(
        start_date=ably_review_scraping_config.get_scraping_start_date(),
        end_date=ably_review_scraping_config.get_scraping_end_date(),
        delimiter=LOCAL_PERIOD_DIRECTORY_NAME_DELIMITER,
        base_path=build_local_shopping_mall_platform_data_directory_path(
            config_registry=local_config_registry,
            platform_name=ABLY_DIRECTORY_NAME,
        ),
    )

    ably_load_spec = ExcelLoadSpec(
        root_path=ably_date_output_directory_path,
        resource_name=POSTPROCESSING_OUTPUT_XLSX_FILE_NAME,
    )

    ably_success_save_spec = ExcelSaveSpec(
        root_path=ably_date_output_directory_path,
        resource_name=FINALIZING_SUCCESS_OUTPUT_XLSX_FILE_NAME,
        overwrite=False,
        pk_column_name=vreview_export_attribute_schema.REVIEW_ID,
        sheet_name='review',
    )
    ably_failed_save_spec = ExcelSaveSpec(
        root_path=ably_date_output_directory_path,
        resource_name=FINALIZING_FAILED_OUTPUT_XLSX_FILE_NAME,
        overwrite=False,
        pk_column_name=vreview_export_attribute_schema.REVIEW_ID,
        sheet_name='review',
    )

    # execution
    finalizing(
        platform=Platform.ABLY,
        export_config=vreview_export_config,
        storage=excel_storage,
        load_spec=ably_load_spec,
        success_save_spec=ably_success_save_spec,
        failed_save_spec=ably_failed_save_spec,
        config_registry=local_config_registry,
    )
