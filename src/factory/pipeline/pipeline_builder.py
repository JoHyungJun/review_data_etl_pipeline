"""
pipeline_builder.py
-------------------

export 정보, 외부 설정값, 환경 정보를 기준으로 실행 대상 파이프라인 판별 및 개별 파이프라인의 객체를 반환하는
공통 메서드를 관리하는 모듈
"""


import logging
from typing import Type, Optional

from core.base.pipeline.base_process_pipeline import BaseProcessPipeline
from core.config.model.config_registry import ConfigRegistry
from domain.export.export import Export
from entry.environment import Environment
from factory.pipeline.constant.deploy_pipeline_factory_mapping import DEPLOY_PIPELINE_FACTORY_MAPPING
from factory.pipeline.constant.export_pipeline_mapping import EXPORT_PROCESS_PIPELINE_MAPPING
from error.config import ConfigNotAvailableError
from factory.pipeline.constant.local_pipeline_factory_mapping import LOCAL_PIPELINE_FACTORY_MAPPING


def export_pipeline_builder(
        export: Export,
        config_registry: ConfigRegistry,
        environment: Environment,
) -> list[BaseProcessPipeline]:
    """
    export 정보, 외부 설정값, 환경 정보를 기준으로 실행 대상 파이프라인 판별 및 개별 파이프라인의 객체를 반환

    주의 사항
    - 해당 메서드는 파이프라인 조립, 프로젝트 구조 (data, output path) 등이
      외부 설정값 (ConfigRegistry) 을 활용한 내재된 규칙에 의해 강제되는 factory 메서드를 활용
      따라서 별도의 path 설정 혹은 pipeline spec 의 정의가 필요한 경우 해당 메서드의 이용을 금지

    :param export: export 정보 Export
    :param config_registry: 설정값이 담긴 인스턴스 ConfigRegistry
    :param environment: 애플리케이션 실행 환경 정보 Environment
    :return: 대상 export 별 지원하는 파이프라인 인스턴스 list[BaseProcessPipeline]
    """

    target_pipeline_types = EXPORT_PROCESS_PIPELINE_MAPPING.get(export)

    if target_pipeline_types is None:
        logging.debug(
            f"[FORMAT] process=export_pipeline_builder, export_platform={export.value}: "
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
            target_pipeline_instance = get_pipeline_instance(
                pipeline_type=target_pipeline_type,
                config_registry=config_registry,
                environment=environment,
            )

            if target_pipeline_instance is None:
                raise ValueError(
                    f"{cur_platform_id} 플랫폼의 인스턴스화 메서드가 정의되지 않았습니다. 코드를 확인해주세요."
                )

            pipelines.append(target_pipeline_instance)

        # 파이프라인 진행에 필요한 설정값이 하나라도 없을 경우, 해당 파이프라인을 진행하지 않는 것으로 판단
        except ConfigNotAvailableError as e:
            logging.warning(
                f"[SKIP] platform={cur_platform_id}: "
                f"Some values are not defined in config registry - {str(e)}"
            )
            continue

    return pipelines


def get_pipeline_instance(
        pipeline_type: Type[BaseProcessPipeline],
        config_registry: ConfigRegistry,
        environment: Environment,
) -> Optional[BaseProcessPipeline]:
    """
    XXX(환경)_PIPELINE_FACTORY_MAPPING 에 매핑된 인스턴스화 메서드를 기반으로
    해당하는 pipeline_type 의 인스턴스를 반환

    주의 사항
    - XXX_PIPELINE_FACTORY_MAPPING 에 매핑되지 않은 파이프라인 type 일 경우 None 반환

    :param pipeline_type: 대상 파이프라인 클래스 Type[BaseProcessPipeline]
    :param config_registry: 설정값이 담긴 인스턴스 ConfigRegistry
    :param environment: 애플리케이션 실행 환경 정보 Environment
    :return: 대상 파이프라인 인스턴스 BaseProcessPipeline
    """

    # 환경별 분기
    initialize_method = None
    if environment == Environment.LOCAL:
        initialize_method = LOCAL_PIPELINE_FACTORY_MAPPING.get(pipeline_type)

    elif environment == Environment.DEPLOY:
        initialize_method = DEPLOY_PIPELINE_FACTORY_MAPPING.get(pipeline_type)

    else:
        raise RuntimeError(
            f"미구현 환경변수로 실행되었습니다. 코드를 확앤해주세요. : {environment}"
        )

    if initialize_method is None:
        return None

    return initialize_method(config_registry)
