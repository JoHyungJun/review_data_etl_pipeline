"""
export_pipeline_applier.py
--------------------------

외부 설정값을 기준으로 실행 대상 파이프라인 판별 및 개별 파이프라인의 객체를 반환하는
공통 메서드를 관리하는 모듈

해당 모듈은 EXPORT_PROCESS_PIPELINE_MAPPING 매핑 정보 및 외부 설정값를 통해
{export: 파이프라인} 조합에서 실행 대상 파이프라인 판별 및 객체를 반환
"""


import logging

from core.base.pipeline.base_process_pipeline import BaseProcessPipeline
from core.base.pipeline.base_required_spec_process_pipeline import BaseRequiredSpecProcessPipeline
from core.config.model.config_registry import ConfigRegistry
from domain.export.export import Export
from entry.orchestration.export_pipeline_mapping import EXPORT_PROCESS_PIPELINE_MAPPING
from error.config import ConfigNotAvailableError


def export_pipeline_applier(
        export: Export,
        config_registry: ConfigRegistry,
) -> list[BaseProcessPipeline]:
    target_pipeline_types = EXPORT_PROCESS_PIPELINE_MAPPING.get(export)

    if target_pipeline_types is None:
        logging.debug(
            f"[FORMAT] process=export_pipeline_applier, export_platform={export.value}: "
            f"Not found export in export pipeline mapping"
        )
        return []

    pipelines = []
    for target_pipeline_type in target_pipeline_types:

        # 외부 설정값에 해당하는 section 정보가 없다면 해당 파이프라인을 진행하지 않는 것으로 판단하고 continue
        cur_platform_id = target_pipeline_type.get_platform().get_platform_id()
        if not config_registry.has_config_data_section(cur_platform_id):
            continue

        try:
            if issubclass(target_pipeline_type, BaseRequiredSpecProcessPipeline):
                pipelines.append(
                    target_pipeline_type.from_config_registry(config_registry)
                )
            else:
                pipelines.append(target_pipeline_type())

        # 파이프라인 진행에 필요한 설정값이 하나라도 없을 경우, 해당 파이프라인을 진행하지 않는 것으로 판단
        except ConfigNotAvailableError as e:
            logging.warning(
                f"[SKIP] platform={cur_platform_id}: "
                f"Some values are not defined in config registry - {str(e)}"
            )
            continue

    return pipelines
