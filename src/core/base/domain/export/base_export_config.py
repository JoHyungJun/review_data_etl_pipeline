"""
base_export_config.py
---------------------

export 대상 플랫폼별 최종 산출물 포맷 정보 관리의 기반이 되는 설정 추상 클래스 설정 모듈
"""


import pandas as pd
from abc import ABC, abstractmethod
from typing import Type, Optional

from core.base.schema.attribute.base_export_attribute_schema import BaseExportAttributeSchema
from core.base.storage.base_storage import BaseStorage
from core.base.storage.spec.base_save_spec import BaseStorageSaveSpec
from core.config.model.config_registry import ConfigRegistry
from domain.platform.platform import Platform
from process.core.preprocess.preprocessing.model.context.source_data_context import SourceDataContext


class BaseExportConfig(ABC):
    """
    export 대상 플랫폼별 최종 산출물 포맷 정보 관리의 기반이 되는 설정 추상 클래스

    - export 대상 플랫폼 정보 구현 강제
    - export 결과물 포맷 구조 (BaseAttributeSchema) 구현 강제
    - export 결과물 포맷 관련 전처리 메서드 구현 강제 (직접 구현 대신 외부에 선언한 플랫폼별 전처리 로직 반환을 권고)
    - export 마지막 비즈니스 로직 메서드 구현 강제
    """

    @abstractmethod
    def get_export_kor_name(self) -> str:
        pass

    @abstractmethod
    def get_export_eng_name(self) -> str:
        pass

    @abstractmethod
    def get_attribute_schema(self) -> Type[BaseExportAttributeSchema]:
        pass

    @abstractmethod
    def apply_export_preprocessing(
            self,
            target_platform: Platform,
            export_formatted_df: pd.DataFrame,
            source_data_context: SourceDataContext,
    ) -> pd.DataFrame:
        """
        데이터 (df) 에 export 별 추가적인 전처리 로직을 적용하고 반환

        주의 사항
        - 해당 메서드는 이후 적용될 모든 로직에서의 기준점이 되므로,
          특정 컬럼의 데이터들에 특수한 데이터 타입을 적용하려면 반드시 이 곳에서 처리해야 하며,
          이 단계 이후 개별 컬럼의 데이터 타입은 변경되지 않는 것을 전제함

          (ex. 날짜/시간 관련 컬럼에 대해 datetime 타입을 부여하고 싶다면,
               df 의 관련 컬럼 데이터들을 파싱 후 return 해야 함)

          이렇게 설정된 데이터 타입은 이후 query, sort, indexing 등에서 활용
          (단, datetime.time 처럼, 시간에 대한 데이터 타입은 엑셀, DB 등에서 정식 포맷으로 인정 받지 못하므로 str 로 save 됨)

        - 해당 메서드는 export schema 컬럼명 포맷으로 rename 된 df 와,
          데이터 수집에 사용된 전체 데이터를 포함하며 개별 schema 포맷 (prefixed) 으로 컬럼명을 가지는 join df 를 이용하여
          export 별 추가 전처리 로직을 적용하는 것에 목적이 있으므로,
          파라미터 및 context 내부의 df 및 attribute schema 의 변경을 금함

        :param target_platform: 데이터 수집 플랫폼 정보 관련 Platform
        :param export_formatted_df: export schema 기준 컬럼명이 포맷팅된 pandas.DataFrame
        :param source_data_context:
            수집된 전체 데이터 및 컬럼명으로 활용되는 개별 schema (prefixed) 을 관리하는 SourceDataContext
        :return: export 플랫폼별 전처리 적용된 pandas.DataFrame
        """

        pass

    @abstractmethod
    def apply_export_finalizing(
            self,
            df: pd.DataFrame,
            storage: BaseStorage,
            success_save_spec: BaseStorageSaveSpec,
            failed_save_spec: BaseStorageSaveSpec,
            config_registry: Optional[ConfigRegistry],
    ) -> pd.DataFrame:
        """
        export 별 마지막 비즈니스 로직 수행 및 데이터 save

        파이프라인을 통과한 데이터에 대해
        export 별 마지막 비즈니스 로직 (포맷팅, API 전송, 최종 결과물 save 등) 수행 후
        성공/실패 여부에 따라 다른 경로에 결과물 데이터 save

        주의 사항
        - 별도의 비즈니스 처리 로직이 필요하지 않은 export 의 경우,
          별도의 추가 로직 없이 파라미터 df 의 단순 save 및 반환을 권고

        :param df: finalize 대상 pandas.DataFrame
        :param storage: 저장소 환경별 save/load 로직을 가진 BaseStorage
        :param success_save_spec: 저장소 환경별 finalize 성공 데이터 save 관련 세부 설정값을 가진 BaseStorageSaveSpec
        :param failed_save_spec: 저장소 환경별 finalize 실패 데이터 save 관련 세부 설정값을 가진 BaseStorageSaveSpec
        :param config_registry: finalize 에서 활용할 외부 설정값 관리 객체 Optional[ConfigRegistry]
        :return: finalize 성공 데이터 pandas.DataFrame
        """

        pass
