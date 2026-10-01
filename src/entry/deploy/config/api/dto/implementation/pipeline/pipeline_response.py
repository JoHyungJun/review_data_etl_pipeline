"""
pipeline_response.py
--------------------

pipeline 실행에 필요한 response DTO 클래스 모듈

주의 사항
- 파이프라인 실행 및 성공 결과 데이터는 response 를 통한 직접 전송이 아닌 저장소 path 를 전달하는 것으로 API 규약
"""


from datetime import date, time
from enum import Enum
from typing import Optional

from pydantic import BaseModel

from entry.deploy.config.api.dto.base.base_api_response import BaseSuccessApiResponse


class PipelineStatus(str, Enum):
    SUCCESS = "SUCCESS"
    SKIPPED = "SKIPPED"


class PipelineResult(BaseModel):
    platform: str
    status: PipelineStatus
    message: str

    final_output_path: Optional[str]


class PipelineResponse(BaseSuccessApiResponse):
    shopping_mall_name: str
    export_id: str

    start_date: date
    start_time: time

    end_date: date
    end_time: time

    datas: list[PipelineResult]
