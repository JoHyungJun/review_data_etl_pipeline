"""
pipeline.py
-----------

로컬 환경용 pipeline 실행 단위 모음 모듈
"""


import logging

from core.base.pipeline.base_process_pipeline import BaseProcessPipeline
from domain.export.export import Export
from entry.environment import Environment
from error.config import ConfigNotAvailableError
from factory.config.registry.local import build_local_ini_config_registry
from factory.pipeline.pipeline_builder import export_pipeline_builder
from util.logging_util import run_with_logging


@run_with_logging(
    lambda shopping_mall_name, export_id: {
        "shopping_mall_name": shopping_mall_name,
        "export_id": export_id,
    }
)
def run_pipelines(
        shopping_mall_name: str,
        export_id: str,
) -> None:
    """
    파이프라인 전체 실행부 runner

    :param shopping_mall_name: 프로세스 실행 주체 회사명 str
    :param export_id: export 식별자 str
    :return: 없음
    """

    config_registry = build_local_ini_config_registry()

    pipelines: list[BaseProcessPipeline] = export_pipeline_builder(
        export=Export.from_id(export_id),
        config_registry=config_registry,
        environment=Environment.LOCAL,
    )

    for pipeline in pipelines:
        try:
            pipeline.run_pipeline()

        except ConfigNotAvailableError as e:
            logging.warning(
                f"[SKIP] platform={pipeline.get_platform().get_platform_eng_name()}: "
                f"Some values are not defined in config registry - {str(e)}"
            )
            continue
