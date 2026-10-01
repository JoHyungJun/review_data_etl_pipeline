"""
deploy_pipeline_factory_mapping.py
----------------------------------

배포 환경용 pipeline 별 인스턴스화 메서드 매핑 정보 모듈

주의 사항
- 해당 모듈에서 매핑되는 {파이프라인 type : 인스턴스화 메서드} 정보는 이후 환경 및 확장에 따라 달라질 수 있음
- 해당 모듈에서 매핑되는 인스턴스화 메서드는 ConfigRegistry 를 파라미터로 받는 것을 전제하며,
  이후 추가적인 파라미터가 필요한 경우 해당 매핑 정보 및 생성 함수 구현의 수정이 요구됨
"""


from typing import Type, Callable

from core.base.pipeline.base_process_pipeline import BaseProcessPipeline
from core.config.model.config_registry import ConfigRegistry


DEPLOY_PIPELINE_FACTORY_MAPPING: dict[
    Type[BaseProcessPipeline],
    Callable[[ConfigRegistry], BaseProcessPipeline]
] = {
    # TODO: deploy 용 pipeline spec 정의 및 해당 매핑 정보 작성
}
