"""
validation_utils.py
-------------------

입력값 검증/파싱 관련 util 모듈
"""


from datetime import datetime
from typing import Optional, Union


def get_validated_date_by_str(
        date_str: str,
        validate_format: str = "%Y-%m-%d"
) -> str:
    """
    검증 대상 날짜 문자열을 파라미터 포맷 (validate_format, 기본값: "yyyy-MM-dd") 으로 검증 후 반환

    :param date_str: 날짜 검증 대상 str
    :param validate_format: 날짜 검증 포맷 (기본값: "yyyy-MM-dd") str
    :return: 포맷으로 검증된 날짜 str
    """
    
    try:
        datetime.strptime(date_str, validate_format)
        return date_str
    except ValueError:
        raise ValueError(f"날짜 검증 대상 변수의 포맷이 잘못되었습니다. : {date_str} ({validate_format} 형식에 맞춰주세요)")


def get_validated_time_by_str(
        time_str: str,
        validate_format: str = "%H:%M:%S"
) -> str:
    """
    검증 대상 시간 문자열을 파라미터 포맷 (validate_format, 기본값: "HH:mm:ss") 으로 검증 후 반환

    :param time_str: 시간 검증 대상 str
    :param validate_format: 시간 검증 포맷 (기본값: "HH:mm:ss") str
    :return: 포맷으로 검증된 시간 str
    """

    try:
        datetime.strptime(time_str, validate_format).time()
        return time_str
    except ValueError:
        raise ValueError(f"시간 검증 대상 변수의 포맷이 잘못되었습니다. : {time_str} ({validate_format} 형식에 맞춰주세요)")


def get_validated_and_parsed_unsigned_int(num: Union[int, str]) -> int:
    """
    양의 정수 여부 검증 및 파싱 후 반환

    :param num: 검증 및 파싱 대상 Union[int, str]
    :return: 검증 및 파싱된 양의 정수 변수값 int
    """
    
    try:
        value = int(num)
    except ValueError:
        raise ValueError(f"해당 변수를 정수로 파싱할 수 없습니다. : {num} (정수 값을 넣어주세요)")

    if value <= 0:
        raise ValueError(f"해당 변수는 양의 정수만 가질 수 있습니다. : {num} (양의 정수 값을 넣어주세요)")

    return value


def get_validated_and_parsed_optional_unsigned_int(num: Optional[Union[int, str]]) -> Optional[int]:
    """
    양의 정수 여부 검증 및 파싱 후 반환 (None 허용)

    변수가 None 이라면 검증 및 파싱 없이 None 반환

    :param num: 검증 및 파싱 대상 Optional[Union[int, str]]
    :return: 검증 및 파싱된 양의 정수 변수값 Optional[int]
    """

    if num is None:
        return None

    return get_validated_and_parsed_unsigned_int(num)


def get_validated_and_parsed_float(num: Union[float, str]) -> float:
    """
    실수 여부 검증 및 파싱 후 반환

    :param num: 검증 및 파싱 대상 Union[float, str]
    :return: 검증 및 파싱된 float
    """

    try:
        return float(num)
    except ValueError:
        raise ValueError(f"해당 변수를 실수로 파싱할 수 없습니다. : {num} (실수 값을 넣어주세요)")


def get_validated_between_zero_and_one_float(num: Union[float, str], include_bounds: bool = False) -> float:
    """
    실수 및 0 ~ 1 사이의 값 여부 검증 및 파싱 후 반환
    
    주로 0 ~ 1 사이의 ratio 비율 값인지에 대한 검증에 활용

    :param num: 검증 및 파싱 대상 Union[float, str]
    :param include_bounds: 범위 경계 값 허용 여부 bool
    :return: 검증 및 파싱된 float
    """

    num = get_validated_and_parsed_float(num)

    if 0 <= num <= 1:
        if include_bounds or int(num) != num:
            return num

    raise ValueError(f"해당 변수가 설정된 범위를 벗어났습니다. : {num}")


def get_validated_over_one_float(num: Union[float, str], include_bounds: bool = False) -> float:
    """
    실수 및 1 이상/초과 값 여부 검증 및 파싱 후 반환

    주로 1 이상/초과 ratio 비율 값인지에 대한 검증에 활용

    :param num: 검증 및 파싱 대상 Union[float, str]
    :param include_bounds: 범위 경계 값 허용 여부 bool
    :return: 검증 및 파싱된 float
    """

    num = get_validated_and_parsed_float(num)

    if num >= 1:
        if include_bounds or num != 1:
            return num

    raise ValueError(f"해당 변수가 설정된 범위를 벗어났습니다. : {num}")
