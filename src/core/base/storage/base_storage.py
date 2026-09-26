"""
base_storage.py
---------------

데이터 접근 및 관리 관련 공통 속성 추상 클래스 설정 모듈

데이터 저장소 (ex. Excel, DB 등) 에의 접근 및 관리 (ex. save, load) 기능 제공 인터페이스
"""


from abc import ABC, abstractmethod
import pandas as pd

from core.base.storage.spec.base_load_spec import BaseStorageLoadSpec
from core.base.storage.spec.base_save_spec import BaseStorageSaveSpec
from core.base.storage.spec.base_spec import BaseStorageSpec


class BaseStorage(ABC):
    """
    데이터 접근 및 관리 관련 공통 속성 추상 클래스

    - 접근 대상 데이터들의 최상위 기준 경로 정보 관리
    - 최상위 기준 경로 기반, 데이터 관리 기본 속성 (save, load, exists) 구현 강제
    
    주의 사항
    - storage 는 배치 단위 (Excel 파일, DB table 등) 데이터에 대한 I/O 계층이며,
      개별 단위 데이터의 비즈니스 관리 (update, delete, 조건부 filtering 등) 는 허용하지 않음
    - 경로 (ex. Excel - 파일, DB - 테이블 등) 정보는 파라미터로 전달된 spec 인스턴스로 활용
    - save 의 경우 데이터 중복 방지 및 overwrite 정책은 개별 구현체에서 정의
    - load 의 경우 전체 데이터 기준으로 작동하나, 파라미터로 query 객체가 전달될 시 해당 조건에 의해 동작
      이는 특정 조건의 데이터 load 시 전체 데이터를 불러오지 않는 최적화를 위함
    - 로그 처리를 위해 구현되는 save/load 메서드에 @run_with_logging 어노테이션을 권고함
    """

    @abstractmethod
    def save(self, save_spec: BaseStorageSaveSpec, df: pd.DataFrame) -> None:
        """
        파라미터로 전달된 pandas.DataFrame 을 spec 에 정의된 경로에 save

        동작 방식
        - 이미 존재하는 동일 pk 데이터에 대해 save_spec 의 overwrite 가 True 일 경우 UPDATE, False 일 경우 IGNORE 형태로 save

        :param save_spec: save 상세 정보 BaseStorageSaveSpec
        :param df: save 대상 데이터 pandas.DataFrame
        :return: 없음
        """

        pass

    @abstractmethod
    def load(self, load_spec: BaseStorageLoadSpec) -> pd.DataFrame:
        """
        spec 에 정의된 경로 및 조건으로 저장소 데이터 load
        
        해당 메서드는 여러 검증 로직에 대한 책임을 가지며,
        그 과정에서 에러 발생 시, raise 하거나 None 을 반환하지 않고 빈 pandas.DataFrame 을 반환해야 함

        동작 방식
        - load_spec 의 query 가 None 일 경우 전체 데이터를, None 이 아닐 경우 해당 조건에 맞는 데이터를 load

        :param load_spec: load 관련 세부 정보 설정값을 가진 BaseStorageLoadSpec
        :return: load 대상 데이터를 파싱한 pandas.DataFrame
        """

        pass

    def exists(self, base_spec: BaseStorageSpec) -> bool:
        """
        spec 에 정의된 경로의 존재 및 접속 가능 여부
        
        주의 사항
        - 개별 저장소의 환경 설정에 따라 경로에 대한 검증을 달리 구현해야 함
        - 해당 검증 로직은 spec 에 정의된 전체 경로에 대한 검증을 대상으로 해야 함을 권고

        :param base_spec: 대상 저장소의 정보 BaseStorageSpec
        :return: spec 에 정의된 경로의 존재 및 접속 가능 여부 bool
        """
        
        pass
