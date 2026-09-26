"""
base_load_spec.py
-----------------

저장소 (storage) load 에 활용할 쿼리 관련 공통 속성 클래스 설정 모듈
"""


from dataclasses import dataclass
from typing import Optional, Union

from core.base.query.spec.base_spec import BaseQuerySpec


@dataclass(frozen=True)
class BaseLoadQuerySpec(BaseQuerySpec):
    """
    저장소 (storage) load 쿼리 관련 공통 속성 클래스

    load 쿼리에 공통적으로 필요한 속성 관리

    주의 사항
    - from 의 경우, storage 환경별로 설정의 차이가 존재하기 때문에
      상수로 관리하지 않고 외부 설정값을 통해 활용하길 권고
    """

    # optional
    where: Optional[str]
    group_by: Optional[str]
    order_by: Optional[str]

    # required
    select: Union[str, list[str]] = "*"
