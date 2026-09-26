"""
export.py
---------

export 별 기초 정보를 정의한 Enum 모듈

시스템 내에서 개별 export 를 식별할 수 있는 id 값을 관리함
export 별 파이프라인 실행 등에서 활용

주의 사항
- platform id 값의 경우 식별 정보로, 외부 설정값 비교 등에서 활용되기 때문에,
  해당 플랫폼 관련 로직이 외부 설정값에서 정보를 추출한다면 section key 값을 부여하길 권고
"""


from __future__ import annotations

from enum import Enum

from config.constant.common.name_constants import VREVIEW_SECTION_KEY


class Export(Enum):

    VREVIEW = VREVIEW_SECTION_KEY

    def __init__(self, export_id: str):
        self._export_id = export_id

    def get_platform_id(self) -> str:
        return self._export_id

    @classmethod
    def from_id(cls, export_id: str) -> Export:
        # 해당 클래스에 관리되는 변수 종류가 늘어날 경우, 해당 로직은 재작성되어야 함
        return Export(export_id)