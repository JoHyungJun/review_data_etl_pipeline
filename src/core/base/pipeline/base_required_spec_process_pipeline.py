"""
base_required_spec_process_pipeline.py
--------------------------------------

pipeline spec 으로 구현되는 파이프라인 공통 속성 추상 클래스 설정 모듈
"""


from __future__ import annotations

from abc import abstractmethod

from core.base.pipeline.base_process_pipeline import BaseProcessPipeline
from core.config.model.config_registry import ConfigRegistry


class BaseRequiredSpecProcessPipeline(BaseProcessPipeline):

    @classmethod
    @abstractmethod
    def from_config_registry(
            cls,
            config_registry: ConfigRegistry,
    ) -> BaseRequiredSpecProcessPipeline:
        """
        config registry 기반 BaseRequiredSpecProcessPipeline 인스턴스 생성 후 반환

        외부 설정값을 기반하여 생성자에 필요한 process spec 인스턴스 생성 및
        해당 process spec 을 기반한 BaseRequiredSpecProcessPipeline 인스턴스 반환

        :param config_registry: BaseProcessPipelineSpec 및 BaseRequiredSpecProcessPipeline 인스턴스 초기화에 활용할 외부 설정값 ConfigRegistry
        :return: 초기화된 인스턴스 BaseRequiredSpecProcessPipeline
        """

        pass