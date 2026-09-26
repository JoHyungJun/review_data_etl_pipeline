from typing import Optional

import pandas as pd

from core.base.domain.export.base_export_config import BaseExportConfig
from core.base.storage.base_storage import BaseStorage
from core.base.storage.spec.base_load_spec import BaseStorageLoadSpec
from core.base.storage.spec.base_save_spec import BaseStorageSaveSpec
from core.config.model.config_registry import ConfigRegistry
from domain.platform.platform import Platform
from util.logging_util import run_with_logging, logging_error_event


@run_with_logging(
    lambda *args, **kwargs: (
        {"platform": kwargs["platform"].get_platform_eng_name()}
        if kwargs.get("platform") is not None
        else {}
    )
)
def finalizing(
        platform: Optional[Platform],
        export_config: BaseExportConfig,
        storage: BaseStorage,
        load_spec: BaseStorageLoadSpec,
        success_save_spec: BaseStorageSaveSpec,
        failed_save_spec: BaseStorageSaveSpec,
        config_registry: Optional[ConfigRegistry],
) -> None:
    """
    export 별 마지막 비즈니스 로직 수행 및 데이터 저장

    export config 에 정의되어 있는 export 별 비즈니스 로직을 수행하고 결과 저장

    비즈니스 로직 정의 및 데이터 저장은 개별 export 객체 내부 정의를 따름

    :param platform: finalize 대상 데이터의 플랫폼 정보 Optional[Platform]
                     (로그 처리를 위한 인자이며, 반드시 keyword argument 방식으로 인자를 넘겨야 함)
    :param export_config: finalize 대상 export 정보를 가진 BaseExportConfig
    :param storage: 저장소 환경별 save/load 로직을 가진 BaseStorage
    :param load_spec: 저장소 환경별 finalize 대상 데이터 load 관련 세부 정보 설정값을 가진 BaseStorageLoadSpec
    :param success_save_spec: 저장소 환경별 finalize 성공 데이터 save 관련 세부 설정값을 가진 BaseStorageSaveSpec
    :param failed_save_spec: 저장소 환경별 finalize 실패 데이터 save 관련 세부 설정값을 가진 BaseStorageSaveSpec
    :param config_registry: finalize 에서 활용할 외부 설정값 관리 객체 Optional[ConfigRegistry]
    :return: 없음
    """

    try:
        df = storage.load(load_spec)

        success_df = export_config.apply_export_finalizing(
            df=df,
            storage=storage,
            success_save_spec=success_save_spec,
            failed_save_spec=failed_save_spec,
            config_registry=config_registry,
        )

    except Exception as e:
        logging_error_event(
            exception_instance=e,
            log_message="While export finalizing",
            log_message_detail=str(e),
        )
        raise
