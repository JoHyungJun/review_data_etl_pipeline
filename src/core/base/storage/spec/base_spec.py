"""
base_spec.py
------------

저장소 (storage) 접근에 필요한 세부 속성 및 조건 설정 관련 공통 속성 클래스 설정 모듈
"""


from abc import ABC
from dataclasses import dataclass
from pathlib import Path
from typing import Union


@dataclass(frozen=True)
class BaseStorageSpec(ABC):
    """
    저장소 (storage) 접근 경로 관련 공통 속성 클래스

    storage 의 구현체 종류 (ex. Excel, DB 등) 에 맞는 추가적인 내부 속성 구현 권고
    """

    # 상위 root 저장소 경로 (ex. Excel -> 디렉토리 경로 / DB -> 연결 엔드포인트)
    root_path: Union[Path, str]

    # 최소 단위 저장소 식별자 (ex. Excel -> 파일명 / DB -> 테이블명)
    resource_name: str

    def get_full_path(self) -> Union[Path, str]:
        """
        해당 spec 인스턴스가 관리하는 데이터 단위 (저장소) 의 전체 경로를 반환

        주의 사항
        - 해당 메서드로 반환되는 경로는 존재 여부가 검증되지 않은 경로로, 단순 정보 확인용이며,
          해당 경로의 저장소 검증을 위한 메서드로는 storage 인스턴스의 exists() 활용을 권고

        :return: 해당 spec 인스턴스의 관리 대상 데이터 단위 전체 경로 Path
        """

        return Path(self.root_path) / Path(self.resource_name)
