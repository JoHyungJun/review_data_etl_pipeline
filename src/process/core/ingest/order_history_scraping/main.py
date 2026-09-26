"""
main.py
-------

order_history_scraping 실행부

개발 환경에서의 통합 테스트를 위한 수동 진입점 모듈이며,
하나의 대표 시나리오 조합 (environment: shopping mall - platform - export) 를
실제 데이터 기반으로 테스트 및 실행, 검증함
"""


from config.constant.name_constants import ORDER_HISTORY_SCRAPING_OUTPUT_XLSX_FILE_NAME, ABLY_DIRECTORY_NAME
from core.common.bootstrap import run_bootstrap
from domain.platform.platform import Platform
from factory.bootstrap.bootstrap_config import LOCAL_BOOTSTRAP_CONFIG
from factory.config.registry.local import build_local_config_registry
from factory.path.local import build_local_shopping_mall_platform_data_directory_path
from factory.process.scraping.order_history_scraping_builder import build_ably_order_history_scraping_config
from core.implementation.storage.excel.spec.excel_save_spec import ExcelSaveSpec
from core.implementation.storage.excel.storage.excel_storage import ExcelStorage
from process.core.ingest.order_history_scraping.order_history_scraping import order_history_scraping
from util.path_util import get_or_create_directory


def main():
    # environment (local) setting
    run_bootstrap(LOCAL_BOOTSTRAP_CONFIG)
    local_config_registry = build_local_config_registry()
    excel_storage = ExcelStorage()

    # source platform (ably) setting
    ably_order_history_scraping_config = build_ably_order_history_scraping_config(local_config_registry)

    ably_data_directory_path = get_or_create_directory(
        full_path=build_local_shopping_mall_platform_data_directory_path(
            config_registry=local_config_registry,
            platform_name=ABLY_DIRECTORY_NAME,
        ),
    )

    ably_save_spec = ExcelSaveSpec(
        root_path=ably_data_directory_path,
        resource_name=ORDER_HISTORY_SCRAPING_OUTPUT_XLSX_FILE_NAME,
        overwrite=False,
        pk_column_name=ably_order_history_scraping_config.get_mapped_pk_attribute_name(),
    )

    # execution
    order_history_scraping(
        platform=Platform.ABLY,
        scraping_config=ably_order_history_scraping_config,
        storage=excel_storage,
        save_spec=ably_save_spec,
    )


if __name__ == "__main__":
    main()
