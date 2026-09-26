"""
excel_save_spec.py
------------------

Excel (storage) 접근 및 저장에 필요한 세부 속성 설정 관련 공통 속성 클래스 설정 모듈
"""


from dataclasses import dataclass

from core.base.storage.spec.base_save_spec import BaseStorageSaveSpec


@dataclass(frozen=True)
class ExcelSaveSpec(BaseStorageSaveSpec):
    """
    Excel (storage) 접근 및 저장에 필요한 세부 속성 설정 관련 공통 속성 클래스
    """

    # 데이터 save 에 활용될 pk 로 사용할 Excel 컬럼명
    pk_column_name: str

    # 데이터를 save 할 대상 시트명
    sheet_name: str = "Sheet1"
