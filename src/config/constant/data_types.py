"""
data_types.py
-------------

스키마 검증 및 파싱 로직에서의 변수별 데이터 타입 판별 기준 정의 Enum 모듈

API 호출 및 주요 내부 로직에서 사용되는 설정값에 대해
각 변수에 자료형을 부여하고, 해당 자료형별 파싱 함수를 적용하기 위해 활용
"""


from enum import Enum
from typing import Optional, Any, Union


class DataType(str, Enum):
    """
    필수 설정값 변수에 대해 부여할 커스텀 자료형을 모아 놓은 문자열 기반 Enum
    개별 타입은 개별 파싱 함수 (get_parsed_value_by_data_type) 와 직접적으로 연결됨
    """

    STR = "str"
    UNSIGNED_INT = "unsigned_int"
    FLOAT = "float"
    DATE = "date"
    TIME = "time"
    DATETIME = "datetime"

    def __str__(self):
        return self.value

    def __repr__(self):
        return f"{self.__class__.__name__}.{self.name}"


def get_parsed_value_by_data_type(
        value: Optional[Union[str, int, float]],
        data_type: 'DataType',
) -> Optional[Any]:
    """
    파라미터 DataType 자료형별로 다른 파싱 메서드를 적용하여
    파라미터 입력값을 파싱하고 반환

    :param value: 파싱 대상값
    :param data_type: 파싱 대상 DataType 커스텀 자료형
    :return: 파싱 및 검증된 변수값
    """

    # 순환 참조 문제로 인한 lazy import
    from util.validate_util import (
        get_validated_and_parsed_unsigned_int,
        get_validated_and_parsed_float,
        get_validated_date_by_str,
        get_validated_time_by_str,
    )

    if value is None:
        return None

    if data_type == DataType.STR:
        return str(value)

    if data_type == DataType.UNSIGNED_INT:
        return get_validated_and_parsed_unsigned_int(value)

    if data_type == DataType.FLOAT:
        return get_validated_and_parsed_float(value)

    if data_type == DataType.DATE:
        return get_validated_date_by_str(value)

    if data_type == DataType.TIME:
        return get_validated_time_by_str(value)
