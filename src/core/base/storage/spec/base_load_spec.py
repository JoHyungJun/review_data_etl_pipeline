"""
base_load_spec.py
-----------------

저장소 (storage) 접근 및 load 에 필요한 세부 속성 및 조건 설정 관련 공통 속성 클래스 설정 모듈
"""


from dataclasses import dataclass
from typing import Optional

from core.base.query.spec.base_load_spec import BaseLoadQuerySpec
from core.base.storage.spec.base_spec import BaseStorageSpec


@dataclass(frozen=True)
class BaseStorageLoadSpec(BaseStorageSpec):
    """
    저장소 (storage) 접근 및 load 전략 관련 공통 속성 클래스

    storage 의 구현체 종류 (ex. Excel, DB 등) 에 맞는 추가적인 내부 속성 구현 권고

    주의 사항
    - 불러올 데이터 조건에 대한 쿼리 정보는 load query spec 객체를 통해 전달되며,
      FROM 에 대한 정보는 환경에 맞는 XXXQueryBuilder 를 활용하여 파라미터를 통해 삽입해야 함
    - load query spec 가 None 일 경우, 개별 XXXQueryBuilder 가 이에 대한 처리 책임을 가지며,
      일반적으로 와일드카드 (SELECT *) 쿼리를 반환하도록 해야 함
    """

    # 데이터 load 의 최적화를 위해 설정되는, 불러올 데이터에 대한 조건 관련 query spec
    # 개별 storage 가 공통 정보를 활용하여 환경별 상이한 구현 책임을 가짐
    load_query_spec: Optional[BaseLoadQuerySpec] = None
