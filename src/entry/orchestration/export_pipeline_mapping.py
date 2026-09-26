"""
export_pipeline_mapping.py
--------------------------

export 기준마다 다르게 수행되어야 할 파이프라인 조합을 관리하는 모듈

해당 모듈은 {export: 해당 export 가 처리할 수 있는 파이프라인 list} 매핑 정보만을 관리하며,
호출 및 사용은 export_pipeline_applier() 메서드를 통해야 함
"""


from typing import Type

from core.base.pipeline.base_process_pipeline import BaseProcessPipeline
from domain.export.export import Export
from domain.platform.ably.pipeline.pipeline import AblyToVReviewProcessPipeline
from domain.platform.coupang.pipeline.pipeline import CoupangToVReviewProcessPipeline


EXPORT_PROCESS_PIPELINE_MAPPING: dict[
    Export, list[Type[BaseProcessPipeline]]
] = {
    Export.VREVIEW: [AblyToVReviewProcessPipeline, CoupangToVReviewProcessPipeline],
}
