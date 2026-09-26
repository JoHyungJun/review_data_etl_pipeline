"""
export_config.py
----------------

VReview 최종 산출물 포맷 정보 관리 설정 클래스 모듈
"""


import math

import pandas as pd
from typing import Type, Optional

from core.base.domain.export.base_export_config import BaseExportConfig
from core.base.schema.attribute.base_export_attribute_schema import BaseExportAttributeSchema
from core.base.storage.base_storage import BaseStorage
from core.base.storage.spec.base_save_spec import BaseStorageSaveSpec
from core.config.constant.schema_constants import VREVIEW
from core.config.model.config_registry import ConfigRegistry
from domain.export.vreview.schema.export.export_attribute_schema import VReviewExportAttributeSchema
from domain.platform.platform import Platform
from domain.platform.vreview.api.file_uploading_config import VreviewFileUploadingConfig
from factory.process.uploading.file_uploading_builder import build_vreview_file_uploading_config
from process.core.preprocess.preprocessing.model.context.source_data_context import SourceDataContext
from process.core.preprocess.preprocessing.preprocessor.export.vreview.vreview_preprocessor import vreview_export_preprocessing
from util.api_util import get_expected_status_response_safely_with_retries
from util.excel_util import get_excel_binary_from_dataframe
from util.logging_util import logging_error_event, logging_file_event


class VReviewExportConfig(BaseExportConfig):
    """
    VReview 최종 산출물 포맷 정보 관리 설정 클래스

    - 플랫폼 정보 관리
    - 최종 산출물 포맷 정보 관리
    - 최종 산출물 포맷에 맞는 전처리 메서드 관리
    - 최종 산출물 finalize 및 save 정보 반환
    """

    def __init__(self):
        self._platform = Platform.VREVIEW
        self._attribute_schema = VReviewExportAttributeSchema
        self._file_uploading_api_config = VreviewFileUploadingConfig

    def get_export_kor_name(self) -> str:
        return self._platform.get_platform_kor_name()

    def get_export_eng_name(self) -> str:
        return self._platform.get_platform_eng_name()

    def get_attribute_schema(self) -> Type[BaseExportAttributeSchema]:
        return self._attribute_schema

    def apply_export_preprocessing(
            self,
            target_platform: Platform,
            export_formatted_df: pd.DataFrame,
            source_data_context: SourceDataContext,
    ) -> pd.DataFrame:
        return vreview_export_preprocessing(
            target_platform=target_platform,
            export_formatted_df=export_formatted_df,
            source_data_context=source_data_context,
        )

    def apply_export_finalizing(
            self,
            df: pd.DataFrame,
            storage: BaseStorage,
            success_save_spec: BaseStorageSaveSpec,
            failed_save_spec: BaseStorageSaveSpec,
            config_registry: Optional[ConfigRegistry],
    ) -> pd.DataFrame:
        """
        최종 데이터에 대한 VReview API 전송 및
        API 전송 성공 데이터 save 및 반환

        해당 로직은 VReview export 관련 강결합을 전제하여 작성되어 있으며,
        VReview export finalize 관련 비즈니스 로직, 포맷, 정보는 모두 해당 메서드에 작성됨

        동작 방식
        - 파라미터 df 를 chunk size (VReview API 가 허용하는 최대 이하의 크기) 만큼씩 분리
        - VReview API 전송 및 성공/실패 여부로 데이터 관리
        - API 전송에 성공한 데이터 df 반환

        주의 사항
        - success save spec 위치에는 API 전송에 성공한 데이터들이 save 되며,
          API 전송에 성공한 데이터가 하나도 없더라도 빈 파일 자체를 save

        - failed save spec 위치에는 API 전송에 실패한 데이터들이 save 되며,
          만약 API 전송에 실패한 데이터가 하나도 없다면 파일 자체를 save 하지 않고
          실패 데이터 파일에 대한 접근 및 retry 는 이를 활용하는 외부에서 파일 존재 여부 확인 등의 책임을 가짐

        :param df: finalize 대상 pandas.DataFrame
        :param storage: 저장소 환경별 save/load 로직을 가진 BaseStorage
        :param success_save_spec: 저장소 환경별 비즈니스 로직 성공 데이터 save 관련 세부 설정값을 가진 BaseStorageSaveSpec
        :param failed_save_spec: 저장소 환경별 비즈니스 로직 실패 데이터 save 관련 세부 설정값을 가진 BaseStorageSaveSpec
        :param config_registry: finalize 에서 활용할 외부 설정값 관리 객체 ConfigRegistry
        :return: finalize 성공 데이터 pandas.DataFrame
        """

        if config_registry is None:
            raise ValueError(
                "브이리뷰의 finalizing 단계에선 외부 설정값이 반드시 필요합니다. 코드를 확인해주세요."
            )

        # 외부 설정값 추출
        split_chunk_size = config_registry.get_value(
            section_key=VREVIEW.SECTION_KEY,
            option_name=VREVIEW.SPLIT_CHUNK_SIZE,
        )

        max_chunk_size = 500
        if split_chunk_size > max_chunk_size:
            raise ValueError(
                f"브이리뷰 api 전송은 최대 {max_chunk_size} 개를 넘지 않아야 합니다. 설정 파일 혹은 코드를 확인해주세요."
            )

        file_uploading_api_config = build_vreview_file_uploading_config(config_registry)

        # formatting
        sorted_df = df.sort_values(
            by=self._attribute_schema.PRODUCT_ID,
            kind="stable",
        ).reset_index(drop=True)

        # splitting & api 호출
        total_chunk_count = math.ceil(len(sorted_df) / split_chunk_size)
        padding = len(str(total_chunk_count))

        failed_dfs = []
        success_dfs = []
        for file_index, chunk_start in enumerate(
                range(0, len(sorted_df), split_chunk_size),
                start=1,
        ):
            chunk_df = sorted_df.iloc[
                chunk_start: chunk_start + split_chunk_size
            ].copy()

            try:
                file_name = (
                    f"vreview_upload_{self.get_export_eng_name()}_"
                    f"{file_index:0{padding}d}_of_{total_chunk_count:0{padding}d}.xlsx"
                )
                file_binary = get_excel_binary_from_dataframe(chunk_df)

                file = file_uploading_api_config.get_request_file(
                    file_name=file_name,
                    file_binary=file_binary,
                )

                response = get_expected_status_response_safely_with_retries(
                    method=file_uploading_api_config.get_method(),
                    base_url=file_uploading_api_config.get_base_url(),
                    headers=file_uploading_api_config.get_headers(),
                    files=file,
                    expected_status_codes=file_uploading_api_config.get_api_expected_success_status_codes(),
                )

            except Exception as e:
                logging_error_event(
                    exception_instance=e,
                    log_metadata={"file_index": file_index},
                    log_message="While upload chunked reviews",
                    log_message_detail=str(e)
                )

                failed_dfs.append(chunk_df)
                continue

            else:
                if response is None:
                    failed_dfs.append(chunk_df)
                else:
                    success_dfs.append(chunk_df)

        if failed_dfs:
            failed_df = pd.concat(failed_dfs, ignore_index=True)

            storage.save(
                save_spec=failed_save_spec,
                df=failed_df,
            )
            logging_file_event(
                file_path=failed_save_spec.get_full_path(),
                log_prefix="SAVE",
                df=failed_df,
            )

        # success 데이터가 존재하지 않은 파일을 저장할 때에도 컬럼을 유지하기 위한 로직
        success_df = (
            pd.concat(success_dfs, ignore_index=True)
            if success_dfs
            else sorted_df.iloc[0:0].copy()
        )

        storage.save(
            save_spec=success_save_spec,
            df=success_df,
        )
        logging_file_event(
            file_path=success_save_spec.get_full_path(),
            log_prefix="SAVE",
            df=success_df,
        )

        return success_df
