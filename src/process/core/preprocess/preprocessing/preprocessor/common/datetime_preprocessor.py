"""
datetime_preprocessor.py
------------------------

날짜/시간 포맷팅/계산 관련 util preprocessor 모듈
"""


import logging

import pandas as pd
from typing import Optional

from util.datetime_util import safe_parse_timestamp
from util.logging_util import logging_error_event


def split_datetime_column(
        df: pd.DataFrame,
        datetime_column_name: Optional[str],
        target_date_column_name: str,
        target_time_column_name: str,
) -> pd.DataFrame:
    """
    DataFrame 의 일시 데이터를 날짜/시간으로 분리하고 두 컬럼에 나누어 저장 후 반환

    :param df: 분리 대상 데이터 pandas.DataFrame
    :param datetime_column_name: 일시에 해당하는 컬럼명 str
    :param target_date_column_name: 새롭게 저장할 날짜에 해당하는 컬럼명 str
    :param target_time_column_name: 새롭게 저장할 시간에 해당하는 컬럼명 str
    :return: 분리 후의 데이터 pandas.DataFrame
    """

    # validate
    if datetime_column_name is None:
        logging.debug(
            f"[FORMAT] process=split_datetime_column, "
            f"parameter={datetime_column_name}: "
            f"Invalid value in parameter - target column name must not be none"
        )
        return df

    if datetime_column_name not in df.columns:
        logging.warning(
            f"[FORMAT] process=split_datetime_column, "
            f"parameter={datetime_column_name}: "
            f"Not found required column name in dataframe"
        )
        return df

    if df[datetime_column_name].replace('', pd.NA).isna().all():
        logging.warning(
            f"[FORMAT] process=split_datetime_column, "
            f"parameter={datetime_column_name}: "
            f"No valid data found - target column has only NaN or empty values"
        )
        return df

    if target_date_column_name is None or target_time_column_name is None:
        logging.warning(
            f"[FORMAT] process=split_datetime_column, "
            f"parameter=[{target_date_column_name}, {target_time_column_name}]: "
            f"Invalid value in parameter - new column name must not be none"
        )
        return df

    if target_date_column_name in df.columns or target_time_column_name in df.columns:
        logging.warning(
            f"[FORMAT] process=split_datetime_column, "
            f"parameter=[{target_date_column_name}, {target_time_column_name}]: "
            f"Invalid value in parameter - target columns already in df columns"
        )

    try:
        df[datetime_column_name] = df[datetime_column_name].apply(safe_parse_timestamp)
        df[target_date_column_name] = df[datetime_column_name].dt.date
        df[target_time_column_name] = df[datetime_column_name].dt.time
    except (ValueError, TypeError) as e:
        logging_error_event(
            log_level="critical",
            log_prefix="PARSE",
            exception_instance=e,
            log_metadata={
                'target_header': f'{datetime_column_name}'
            },
            log_message="While parsing and splitting datetime",
        )
        raise ValueError(f"{datetime_column_name} 를 날짜와 시간으로 분리하던 중 에러가 발생했습니다. 데이터를 확인해주세요.")

    return df


def parse_date_time_column(
        df: pd.DataFrame,
        date_column_name: str,
        time_column_name: str,
) -> pd.DataFrame:
    """
    DataFrame 의 날짜/시간 데이터를 날짜/시간 데이터 타입으로 파싱 후 반환

    :param df: 변환 대상 pandas.DataFrame
    :param date_column_name: 날짜에 해당하는 컬럼명 str
    :param time_column_name: 시간에 해당하는 컬럼명 str
    :return: 파싱 후의 데이터 pandas.DataFrame
    """

    # validate
    if date_column_name is None or time_column_name is None:
        logging.warning(f"[WARN] parameter=[{date_column_name}, {time_column_name}]: Invalid value in parameter")
        return df

    if date_column_name not in df.columns or time_column_name not in df.columns:
        logging.warning(f"[WARN] parameter=[{date_column_name}, {time_column_name}]: "
                        f"Not found required column name in dataframe")
        return df

    try:
        df[date_column_name] = pd.to_datetime(df[date_column_name], errors='raise').dt.date
        df[time_column_name] = pd.to_datetime(df[time_column_name], errors='raise').dt.time
    except (ValueError, TypeError) as e:
        logging_error_event(
            log_level="critical",
            log_prefix="PARSE",
            exception_instance=e,
            log_metadata={
                'target_header': [f'{date_column_name}', f'{time_column_name}']
            },
            log_message="While parsing each date and time",
        )
        raise Exception(f"'{date_column_name}', '{time_column_name}' 을 파싱하던 중 에러가 발생했습니다. 데이터를 확인해주세요.")

    return df
