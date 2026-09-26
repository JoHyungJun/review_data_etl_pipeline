"""
excel_load_spec.py
------------------

Excel (storage) 접근 및 load 에 필요한 세부 속성 및 조건 설정 관련 공통 속성 클래스 설정 모듈
"""


from dataclasses import dataclass
from typing import Union, Literal

from core.base.storage.spec.base_load_spec import BaseStorageLoadSpec


@dataclass(frozen=True)
class ExcelLoadSpec(BaseStorageLoadSpec):
    """
    Excel (storage) 접근 및 load 에 필요한 세부 속성 및 조건 설정 관련 공통 속성 클래스

    주의 사항
    - sheet_names 는 load 대상 전체 시트명을 적는 것으로,
      "*" 와일드 카드를 통해 전체 시트를 불러오거나,
      단일 시트 str, 혹은 여러 시트 list[str] 를 사용할 수 있음
    """

    # '*' 는 wild card 로 전체 시트 데이터를 가지고 올 때 기본값으로 활용
    sheet_names: Union[str, list[str], Literal["*"]] = '*'
