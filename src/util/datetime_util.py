"""
datetime_util.py
----------------

날짜/시간 포맷팅/계산 관련 util 모듈
"""


import logging
import time
from datetime import datetime, date
from typing import Optional, Any
from urllib.parse import quote

import pandas as pd

from src.util.validate_util import get_validated_date_by_str, get_validated_time_by_str


"""
시간 단위 상수 (milliseconds 기준)
"""
# 기준 밀리초
MILLISECONDS_PER_SECOND = 1000

# 밀리초 기반 일 수
DAY_MILLISECONDS = 24 * 60 * 60 * MILLISECONDS_PER_SECOND
MONTH_MILLISECONDS = 30 * DAY_MILLISECONDS
YEAR_MILLISECONDS = 365 * DAY_MILLISECONDS


def join_date_and_time(
        date_str: str,
        time_str: str,
        delimiter: str = " "
) -> str:
    """
    파라미터 날짜/시간 검증 및 구분자 포함 통합 단일 문자열 반환

    :param date_str: 날짜 (yyyy-MM-dd) str
    :param time_str: 시간 (HH:mm:ss) str
    :param delimiter: 날짜 시간 정보의 구분자 str
    :return: 날짜/구분자/시간 통합 str
    """

    get_validated_date_by_str(date_str)
    get_validated_time_by_str(time_str)
    return f"{date_str}{delimiter}{time_str}"


def encode_date_and_time(
        date_str: str,
        time_str: str,
        delimiter: str = " "
) -> str:
    """
    파라미터 날짜/시간 검증 및 구분자 포함 URL 인코딩된 단일 문자열 반환

    :param date_str: 날짜 (yyyy-MM-dd) str
    :param time_str: 시간 (HH:mm:ss) str
    :param delimiter: 날짜 시간 정보의 구분자 str
    :return: 날짜/구분자/시간 통합 및 인코딩된 str
    """

    get_validated_date_by_str(date_str)
    get_validated_time_by_str(time_str)
    return quote(f"{date_str}{delimiter}{time_str}")


def parse_date_by_str(
        date_str: str,
        parse_format: Optional[str] = None,
) -> Optional[date]:
    """
    str 형식의 날짜 정보를 datetime.date 객체로 변환

    :param date_str: 날짜 str
    :param parse_format: 변환 포맷 (기본값: %Y-%m-%d) str
    :return: 검증 및 변환 성공 여부에 따른 Optional[datetime.date]
    """

    if date_str is None:
        return None

    # 변환 포맷의 기본값
    if parse_format is None:
        parse_format = "%Y-%m-%d"

    return datetime.strptime(date_str, parse_format).date()


def parse_time_by_str(
        time_str: str,
        parse_format: Optional[str] = None,
) -> Optional[time]:
    """
    str 형식의 시간 정보를 datetime.time 객체로 변환

    :param time_str: 시간 str
    :param parse_format: 변환 포맷 (기본값: %H:%M:%S) Optional[str]
    :return: 검증 및 변환 성공 여부에 따른 Optional[datetime.time]
    """

    if time_str is None:
        return None

    # 변환 포맷의 기본값
    if parse_format is None:
        parse_format = "%H:%M:%S"

    return datetime.strptime(time_str, parse_format).time()


def adjust_term_to_safe_limit_ms(
        term_limit_ms: Optional[int],
        ratio: float = 0.8
) -> Optional[int]:
    """
    플랫폼별 API 수집 term 에 안전 비율을 적용하여 반환

    :param term_limit_ms: 플랫폼 term (milliseconds 단위) Optional[int]
    :param ratio: 안전 비율 (기본값: 80%) float
    :return: 검증 성공 여부에 따른 Optional[int]
    """

    if term_limit_ms is None:
        return None

    safe_ms = int(term_limit_ms * ratio)
    safe_ms = max(DAY_MILLISECONDS, safe_ms)  # 최소 하루 보장
    return safe_ms


def safe_parse_timestamp(timestamp: Any) -> Optional[pd.Timestamp]:
    """
    다양한 자료형 (int/float/str/NaN) 의 일시 정보를 pandas.Timestamp 로 변환 후 반환

    :param timestamp: 변환 대상 timestamp Any
    :return: 분기 및 변환된 Optional[pandas.Timestamp]
    """

    try:
        # 값이 없을 경우
        if pd.isna(timestamp):
            return None

        # millisecond 단위일 경우
        if isinstance(timestamp, (int, float)):
            # 10자리면 sec, 13자리면 milli sec
            if timestamp > 1e12:
                ts_converted = pd.to_datetime(timestamp, unit='ms', errors='coerce')
            elif timestamp > 1e10:
                # 일부 극단적으로 큰 값 (10자리 초보다 큰 값) 처리
                ts_converted = pd.to_datetime(timestamp // 1000, unit='s', errors='coerce')
            else:
                ts_converted = pd.to_datetime(timestamp, unit='s', errors='coerce')
            return ts_converted

        # 문자열 등 일반 형식일 경우
        else:
            return pd.to_datetime(timestamp, errors='coerce')

    # 분기에 아무것도 해당되지 않는다면 None 반환
    except Exception as e:
        logging.warning(f"[FAILED] Failed to parse timestamp '{timestamp}': {e}")
        return None


def get_current_datetime() -> datetime:
    """
    현 시점의 일시 정보를 datetime 형태로 반환

    :return: 현 시점의 일시 정보 datetime
    """

    return datetime.fromtimestamp(time.time())
