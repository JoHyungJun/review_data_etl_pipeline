"""
main.py
-------

postprocessing 의 실행부

개발 환경에서의 통합 테스트를 위한 수동 진입점 모듈이며,
하나의 대표 시나리오 조합 (environment: shopping mall - platform - export) 를
실제 데이터 기반으로 테스트 및 실행, 검증함
"""


from config.constant.common.name_constants import (
    VREVIEW_TO_PLATFORM_PRODUCT_OPTION_MAPPING_XLSX_FILE_NAME,
    PREPROCESSING_OUTPUT_XLSX_FILE_NAME,
    POSTPROCESSING_OUTPUT_XLSX_FILE_NAME,
    ABLY_DIRECTORY_NAME,
    VREVIEW_DIRECTORY_NAME,
)
from core.common.bootstrap import run_bootstrap
from factory.bootstrap.config.local import LOCAL_BOOTSTRAP_CONFIG
from factory.config.registry.local import build_local_ini_config_registry
from factory.path.local import build_local_shopping_mall_platform_data_directory_path
from factory.pipeline.spec.local import LOCAL_PERIOD_DIRECTORY_NAME_DELIMITER
from factory.process.scraping.review_scraping_builder import build_ably_review_scraping_config
from core.base.dataset.dataset_spec import DatasetSpec
from domain.export.vreview.schema.export.export_attribute_schema import VReviewExportAttributeSchema
from domain.platform.platform import Platform
from domain.export.vreview.schema.reference.product_option_mapping_attribute_schema import \
    VReviewProductOptionMappingAttributeSchema
from core.implementation.storage.excel.spec.excel_load_spec import ExcelLoadSpec
from core.implementation.storage.excel.spec.excel_save_spec import ExcelSaveSpec
from core.implementation.storage.excel.storage.excel_storage import ExcelStorage
from process.core.postprocess.postprocessing.postprocessor.common.product_option_remapping import \
    product_option_remapping
from process.core.postprocess.postprocessing.postprocessor.common.sentiment.sentiment_model_applying import \
    sentiment_model_applying
from process.core.postprocess.postprocessing.postprocessor.export.vreview.review_id_hashing import review_id_hashing
from util.column_util import build_indexed_column_name
from util.path_util import get_or_create_date_period_directory


def main():
    # environment (local) setting
    run_bootstrap(LOCAL_BOOTSTRAP_CONFIG)
    local_config_registry = build_local_ini_config_registry()
    excel_storage = ExcelStorage()

    # target export (vreview) setting
    vreview_export_attribute_schema = VReviewExportAttributeSchema

    vreview_product_option_mapping_dataset_spec = DatasetSpec(
        attribute_schema=VReviewProductOptionMappingAttributeSchema,
        load_spec=ExcelLoadSpec(
            root_path=build_local_shopping_mall_platform_data_directory_path(
                config_registry=local_config_registry,
                platform_name=VREVIEW_DIRECTORY_NAME,
            ),
            resource_name=VREVIEW_TO_PLATFORM_PRODUCT_OPTION_MAPPING_XLSX_FILE_NAME,
        ),
    )

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

    # postprocessing input setting
    df = excel_storage.load(
        load_spec=ExcelLoadSpec(
            root_path=ably_date_output_directory_path,
            resource_name=PREPROCESSING_OUTPUT_XLSX_FILE_NAME,
        )
    )

    # execution
    # product_option_remapping
    df = product_option_remapping(
        platform=Platform.ABLY,
        df=df,
        storage=excel_storage,
        product_option_mapping_dataset_spec=vreview_product_option_mapping_dataset_spec,
        product_id_column=vreview_export_attribute_schema.PRODUCT_ID,
        product_name_column=build_indexed_column_name(
            column_name=vreview_export_attribute_schema.PRODUCT_OPTION_NAME,
            index=1,
        ),
        product_option_name_column=build_indexed_column_name(
            column_name=vreview_export_attribute_schema.PRODUCT_OPTION_VALUE,
            index=1,
        ),
    )

    # review_id_hashing
    df = review_id_hashing(
        platform=Platform.ABLY,
        df=df,
        review_id_column=vreview_export_attribute_schema.REVIEW_ID,
        review_created_date_column=vreview_export_attribute_schema.REVIEW_CREATED_DATE,
        review_created_time_column=vreview_export_attribute_schema.REVIEW_CREATED_TIME,
        hashed_review_id_length=16,
    )

    # sentiment_model_applying
    df = sentiment_model_applying(
        platform=Platform.ABLY,
        df=df,
        target_texts_column=vreview_export_attribute_schema.REVIEW_CONTENTS,
    )

    excel_storage.save(
        save_spec=ExcelSaveSpec(
            root_path=ably_date_output_directory_path,
            resource_name=POSTPROCESSING_OUTPUT_XLSX_FILE_NAME,
            overwrite=True,
            pk_column_name=vreview_export_attribute_schema.REVIEW_ID,
            sheet_name='review'
        ),
        df=df,
    )


if __name__ == "__main__":
    main()
