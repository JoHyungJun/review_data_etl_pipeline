"""
pipeline.py
-----------

Coupang review scraping 및 VReview finalizing 파이프라인 설정 모듈

- 파이프라인 관련 config 인스턴스, 경로 등을 정의한 pipeline spec 객체를 주입받아 내부 개별 메서드 구현
- BaseProcessPipeline 를 상속받아 공통 파이프라인 메서드 인터페이스 구현
"""


from pathlib import Path

from core.base.dataset.dataset_spec import DatasetSpec
from core.base.pipeline.base_process_pipeline import BaseProcessPipeline
from domain.platform.coupang.pipeline.model.coupang_process_pipeline_spec import CoupangProcessPipelineSpec
from domain.platform.platform import Platform
from process.core.finalize.finalizing.finalizing import finalizing
from process.core.ingest.review_scraping.review_scraping import review_scraping
from process.core.postprocess.postprocessing.postprocessor.common.product_option_remapping import \
    product_option_remapping
from process.core.postprocess.postprocessing.postprocessor.common.sentiment.sentiment_model_applying import \
    sentiment_model_applying
from process.core.postprocess.postprocessing.postprocessor.export.vreview.review_id_hashing import review_id_hashing
from process.core.preprocess.preprocessing.preprocessing import preprocessing
from util.column_util import build_indexed_column_name
from util.logging_util import run_with_logging


class CoupangToVReviewProcessPipeline(BaseProcessPipeline):
    """
    Coupang review scraping 및 VReview finalizing 파이프라인 설정 클래스

    해당 클래스는 객체 생성에 config registry 가 요구되므로 마커 클래스를 상속
    """

    def __init__(
        self,
        pipeline_spec: CoupangProcessPipelineSpec,
    ):
        self._pipeline_spec = pipeline_spec

    @classmethod
    def get_platform(cls) -> Platform:
        return Platform.COUPANG

    def get_final_output_path(self) -> Path:
        return self._pipeline_spec.finalizing_success_save_spec.get_full_path()

    def run_ingest(self) -> None:
        review_scraping(
            platform=self.get_platform(),
            scraping_config=self._pipeline_spec.review_scraping_config,
            storage=self._pipeline_spec.storage,
            save_spec=self._pipeline_spec.review_scraping_save_spec,
        )

    def run_preprocess(self) -> None:
        preprocessing(
            platform=self._pipeline_spec.platform,
            export_config=self._pipeline_spec.export_config,
            storage=self._pipeline_spec.storage,
            save_spec=self._pipeline_spec.preprocessing_save_spec,
            product_id_mapping_dataset_spec=DatasetSpec(
                self._pipeline_spec.product_id_mapping_attribute_schema,
                self._pipeline_spec.preprocessing_product_id_mapping_load_spec,
            ),
            product_option_mapping_dataset_spec=DatasetSpec(
                self._pipeline_spec.product_option_mapping_attribute_schema,
                self._pipeline_spec.preprocessing_product_option_mapping_load_spec,
            ),
            review_dataset_spec=DatasetSpec(
                self._pipeline_spec.review_scraping_attribute_schema,
                self._pipeline_spec.preprocessing_review_scraping_load_spec,
            ),
        )

    def run_postprocess(self) -> None:
        df = self._pipeline_spec.storage.load(
            load_spec=self._pipeline_spec.preprocessing_load_spec,
        )

        df = product_option_remapping(
            platform=self.get_platform(),
            df=df,
            storage=self._pipeline_spec.storage,
            product_option_mapping_dataset_spec=DatasetSpec(
                self._pipeline_spec.product_option_mapping_attribute_schema,
                self._pipeline_spec.preprocessing_product_option_mapping_load_spec,
            ),
            product_id_column=self._pipeline_spec.postprocessing_product_id_column_name,
            product_name_column=build_indexed_column_name(
                column_name=self._pipeline_spec.postprocessing_product_option_name_column_name,
                index=1,
            ),
            product_option_name_column=build_indexed_column_name(
                column_name=self._pipeline_spec.postprocessing_product_option_value_column_name,
                index=1,
            ),
        )

        df = review_id_hashing(
            platform=self.get_platform(),
            df=df,
            review_id_column=self._pipeline_spec.postprocessing_review_id_column_name,
            review_created_date_column=self._pipeline_spec.postprocessing_review_created_date_column_name,
            review_created_time_column=self._pipeline_spec.postprocessing_review_created_time_column_name,
            hashed_review_id_length=16,
        )

        df = sentiment_model_applying(
            platform=self.get_platform(),
            df=df,
            target_texts_column=self._pipeline_spec.postprocessing_review_contents_column_name,
        )

        self._pipeline_spec.storage.save(
            save_spec=self._pipeline_spec.postprocessing_save_spec,
            df=df,
        )

    def run_finalize(self) -> None:
        finalizing(
            platform=self._pipeline_spec.platform,
            export_config=self._pipeline_spec.export_config,
            storage=self._pipeline_spec.storage,
            load_spec=self._pipeline_spec.postprocessing_load_spec,
            success_save_spec=self._pipeline_spec.finalizing_success_save_spec,
            failed_save_spec=self._pipeline_spec.finalizing_failed_save_spec,
            config_registry=self._pipeline_spec.config_registry,
        )

    @run_with_logging(
        lambda self: {
            "shopping_mall_name": self._pipeline_spec.shopping_mall_name,
            "export_id": self._pipeline_spec.export_config.get_export_eng_name(),
        }
    )
    def run_pipeline(self) -> None:
        self.run_ingest()
        self.run_preprocess()
        self.run_postprocess()
        self.run_finalize()
