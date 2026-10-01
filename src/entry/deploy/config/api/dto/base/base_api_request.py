"""
base_api_request.py
-------------------

HTTP API 에서 애플리케이션 프로세스에 요구되는 기본 request 형태를 정의한 request DTO 관련 추상 클래스 모듈

주의 사항
- 공통 설정부를 제외한 설정값의 경우 configs 에 해당하는 단순 dict 으로 request 를 받으며,
  이는 Extensible Configuration Contract 형태로 adapter 에 의한 처리가 요구됨
- 추가적인 데이터가 요구되는 request 클래스의 경우 해당 클래스의 구조를 유지하며 필요 변수의 추가가 가능하며,
  추가되는 변수의 경우에도 반드시 Section-based Configuration 형태의 구조 (변수: dict[str, Any]) 가 요구됨
"""


from datetime import date, time
from typing import Any

from pydantic import BaseModel

from domain.export.export import Export


class CommonConfig(BaseModel):
    shopping_mall_name: str
    export_id: Export

    start_date: date
    start_time: time

    end_date: date
    end_time: time


class BaseApiRequest(BaseModel):
    common_config: CommonConfig
    configs: dict[str, dict[str, Any]]
