"""
pipeline.py
-----------

배포 환경용 pipeline URL 관련 router 객체 모음 모듈
"""


import logging

from fastapi import APIRouter

from core.base.pipeline.base_process_pipeline import BaseProcessPipeline
from core.config.constant.schema_constants import COMMON
from domain.export.export import Export
from entry.deploy.config.api.dto.implementation.pipeline.pipeline_request import PipelineRequest
from entry.deploy.config.api.dto.implementation.pipeline.pipeline_response import PipelineResult, PipelineResponse, \
    PipelineStatus
from entry.environment import Environment
from error.config import ConfigNotAvailableError
from factory.config.registry.deploy import build_deploy_api_config_registry
from factory.pipeline.pipeline_builder import export_pipeline_builder
from util.logging_util import run_with_logging


# pipeline URL
pipeline_router = APIRouter(
    prefix="/pipeline",
    tags=["pipeline"],
)


@pipeline_router.post(
    "",
    response_model=PipelineResponse,
)
@run_with_logging(
    lambda request: {
        "shopping_mall_name": request.common_config.shopping_mall_name,
        "export_id": request.common_config.export_id.get_export_id(),
    }
)
def run_pipelines(request: PipelineRequest) -> PipelineResponse:
    """
    파이프라인 전체 실행부 API router

    :param request: request 요청된 API 객체 PipelineRequest
    :return: response 응답할 API 객체 PipelineResponse
    """

    config_registry = build_deploy_api_config_registry(request)

    export_id = config_registry.get_value(
        section_key=COMMON.SECTION_KEY,
        option_name=COMMON.EXPORT_ID,
    )
    export = Export.from_id(export_id)

    pipelines: list[BaseProcessPipeline] = export_pipeline_builder(
        export=export,
        config_registry=config_registry,
        environment=Environment.DEPLOY,
    )

    results = []

    for pipeline in pipelines:
        try:
            pipeline.run_pipeline()

            results.append(
                PipelineResult(
                    platform=pipeline.get_platform().get_platform_eng_name(),
                    status=PipelineStatus.SUCCESS,
                    message="Pipeline execution completed successfully",

                    final_output_path=str(pipeline.get_final_output_path()),
                )
            )

        except ConfigNotAvailableError as e:
            logging.warning(
                f"[SKIP] platform={pipeline.get_platform().get_platform_eng_name()}: "
                f"Some values are not defined in config registry - {str(e)}"
            )

            results.append(
                PipelineResult(
                    platform=pipeline.get_platform().get_platform_eng_name(),
                    status=PipelineStatus.SKIPPED,
                    message="Some required configuration is not available",

                    final_output_path=None,
                )
            )

    return PipelineResponse(
        message="Pipeline request completed successfully",

        shopping_mall_name=request.common_config.shopping_mall_name,
        export_id=export_id,

        start_date=request.common_config.start_date,
        start_time=request.common_config.start_time,

        end_date=request.common_config.end_date,
        end_time=request.common_config.end_time,

        datas=results,
    )
