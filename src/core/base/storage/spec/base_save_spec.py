"""
base_save_spec.py
-----------------

저장소 (storage) 접근 및 save 에 필요한 세부 속성 설정 관련 공통 속성 클래스 설정 모듈
"""


from dataclasses import dataclass

from core.base.storage.spec.base_spec import BaseStorageSpec


@dataclass(frozen=True)
class BaseStorageSaveSpec(BaseStorageSpec):
    """
    저장소 (storage) 접근 및 save 전략 설정 관련 추상 클래스

    storage 의 구현체 종류 (ex. Excel, DB 등) 에 맞는 추가적인 내부 속성 구현 권고
    """

    # save 시 이미 저장소에 같은 pk 데이터가 존재한다면, 해당 레코드를 UPDATE 할 것인지 (True), 무시할 것인지 (False) 여부
    overwrite: bool
