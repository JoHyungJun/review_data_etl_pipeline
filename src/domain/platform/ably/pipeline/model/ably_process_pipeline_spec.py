"""
ably_process_pipeline_spec.py
-----------------------------

A-bly 파이프라인 전체 실행에 필요한 관련 속성 모음 클래스 설정 모듈
"""


from dataclasses import dataclass
from typing import ClassVar, Type, Optional

from core.base.domain.export.base_export_config import BaseExportConfig
from core.base.pipeline.base_process_pipeline_spec import BaseProcessPipelineSpec
from core.base.schema.attribute.base_product_id_mapping_attribute_schema import BaseProductIdMappingAttributeSchema
from core.base.schema.attribute.base_product_option_mapping_attribute import BaseProductOptionMappingAttributeSchema
from core.base.storage.base_storage import BaseStorage
from core.base.storage.spec.base_load_spec import BaseStorageLoadSpec
from core.base.storage.spec.base_save_spec import BaseStorageSaveSpec
from core.config.model.config_registry import ConfigRegistry
from domain.platform.ably.api.order_history_scraping_config import AblyOrderHistoryScrapingConfig
from domain.platform.ably.api.review_scraping_config import AblyReviewScrapingConfig
from domain.platform.ably.schema.order_history_scraping_attribute_schema import \
    AblyOrderHistoryScrapingReviewAttributeSchema
from domain.platform.ably.schema.review_scraping_attribute_schema import AblyReviewScrapingReviewAttributeSchema
from domain.platform.platform import Platform
from util.runtime_environment_util import get_recommended_workers_count


@dataclass
class AblyProcessPipelineSpec(BaseProcessPipelineSpec):

    # environment
    shopping_mall_name: Optional[str]
    platform: ClassVar[Platform] = Platform.ABLY
    config_registry: ConfigRegistry

    # common
    storage: BaseStorage
    export_config: BaseExportConfig

    review_scraping_attribute_schema = AblyReviewScrapingReviewAttributeSchema
    order_history_attribute_schema = AblyOrderHistoryScrapingReviewAttributeSchema

    product_id_mapping_attribute_schema: Type[BaseProductIdMappingAttributeSchema]
    product_option_mapping_attribute_schema: Type[BaseProductOptionMappingAttributeSchema]

    # ingest
    review_scraping_config: AblyReviewScrapingConfig
    review_scraping_save_spec: BaseStorageSaveSpec
    review_scraping_load_spec: BaseStorageLoadSpec

    order_history_scraping_config: AblyOrderHistoryScrapingConfig
    order_history_scraping_save_spec: BaseStorageSaveSpec
    order_history_scraping_load_spec: BaseStorageLoadSpec

    # preprocess
    preprocessing_save_spec: BaseStorageSaveSpec
    preprocessing_load_spec: BaseStorageLoadSpec

    preprocessing_review_scraping_load_spec: BaseStorageLoadSpec
    preprocessing_order_history_scraping_load_spec: BaseStorageLoadSpec
    preprocessing_product_id_mapping_load_spec: BaseStorageLoadSpec
    preprocessing_product_option_mapping_load_spec: BaseStorageLoadSpec

    # postprocess
    postprocessing_save_spec: BaseStorageSaveSpec
    postprocessing_load_spec: BaseStorageLoadSpec

    postprocessing_product_id_column_name: str
    postprocessing_product_option_name_column_name: str
    postprocessing_product_option_value_column_name: str
    postprocessing_review_id_column_name: str
    postprocessing_review_created_date_column_name: str
    postprocessing_review_created_time_column_name: str
    postprocessing_review_contents_column_name: str

    # finalize
    finalizing_success_save_spec: BaseStorageSaveSpec
    finalizing_failed_save_spec: BaseStorageSaveSpec

    # execution
    order_history_max_workers: int = get_recommended_workers_count()
