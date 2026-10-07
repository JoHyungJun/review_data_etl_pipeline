"""
column_util.py
--------------

컬럼 관련 util 모듈
"""


import json
import logging
from typing import Any, Union, Optional

import pandas as pd


def date_to_str(date: Any) -> str:
    """
    날짜 데이터를 문자열 포맷 (yyyy-MM-dd) 으로 변환

    :param date: 개별 날짜 데이터 Any
    :return: 변환된 날짜 str
    """

    # pandas.to_datetime() 만으로 거의 모든 케이스가 커버 됨
    try:
        parsed_date = pd.to_datetime(date, errors='coerce')
        return parsed_date.strftime("%Y-%m-%d")
    except Exception as e:
        raise ValueError(f"날짜를 변환하는 과정에서 잘못된 값이 들어왔습니다. 데이터를 확인해주세요. : {date}")


def time_to_str(time: Any) -> str:
    """
    시간 데이터를 문자열 포맷 (HH:mm:ss) 으로 변환
    파라미터가 가질 수 있는 여러 문자형에 대해 Excel save 환경 및 여러 환경을 고려한 분기로 변환

    :param time: 개별 시간 데이터 Any
    :return: 변환된 시간 str
    """

    # Case 1: datetime.time
    if isinstance(time, time):
        try:
            return time.strftime("%H:%M:%S")
        except Exception:
            raise ValueError(
                f"시간을 datetime.time 에서 변환하는 과정에서 문제가 발생했습니다. 데이터를 확인해주세요. : {time}"
            )

    # Case 2: Excel serial number (float or int)
    if isinstance(time, (float, int)):
        try:
            dt = pd.to_datetime(time, unit='d', origin='1899-12-30')
            return dt.strftime("%H:%M:%S")
        except Exception:
            raise ValueError(
                f"시간을 Excel serial number 에서 변환하는 과정에서 문제가 발생했습니다. 데이터를 확인해주세요. : {time}"
            )

    # Case 3: str or etc
    try:
        dt = pd.to_datetime(time, errors='coerce')
        if pd.isna(dt):
            raise ValueError(f"시간 값을 datetime 으로 파싱할 수 없습니다: {time}")
        return dt.strftime("%H:%M:%S")
    except Exception:
        raise ValueError(
            f"시간을 문자열(str)에서 변환하는 과정에서 문제가 발생했습니다. 데이터를 확인해주세요. : {time}"
        )


def combine_title_content(
        row: pd.Series,
        title_column_name: str,
        contents_column_name: str
) -> Optional[str]:
    """
    데이터 개별 행 (레코드) 을 파라미터로 받아 리뷰 내용과 제목을 규칙에 의해 결합하고 반환

    결합 규칙
    - 제목이 None -> 내용만 반환
    - 내용이 None -> 제목만 반환
    - 제목, 내용이 None -> None 반환
    - 제목, 내용이 둘 다 있음
        -> "{제목} {내용}" 둘 다 반환
        -> 단, 제목이 내용의 시작 부와 완전히 겹친다면 내용만 반환

    :param row: 데이터 개별 행 (레코드) pandas.Series
    :param title_column_name: 제목 컬럼명 str
    :param contents_column_name: 내용 컬럼명 str
    :return: 제목, 내용을 규칙에 따라 결합한 Optional[str]
    """

    title = row.get(title_column_name)
    content = row.get(contents_column_name)

    # 둘 다 None 이라면 None 반환
    if pd.isna(title) and pd.isna(content):
        return None

    # 둘 중 하나가 None 이라면 반댓값 반환
    title_str = "" if pd.isna(title) else str(title).strip()
    content_str = "" if pd.isna(content) else str(content).strip()

    # 리뷰 내용의 시작 부와 리뷰 제목이 완전히 동일하다면 내용 반환
    if title_str and content_str.startswith(title_str):
        return content_str if content_str else None

    return " ".join([result for result in [title_str, content_str] if result])


def get_valid_columns_in_df(
        df: pd.DataFrame,
        column_names: list[str],
) -> list[str]:
    """
    파라미터로 전달된 column_names 중
    정상적인 값이면서, df columns 에 존재하는 컬럼들만 반환

    동작 방식
    - None, NotImplemented 컬럼명 제외
    - ' ', '' 컬럼명 제외
    - df 의 컬럼명에 존재하지 않는 컬럼명 제외

    :param df: 대상 pandas.DataFrame
    :param column_names: 검증 대상 컬럼 목록 list[str]
    :return: 정상적 값이면서 df 에 존재하는 컬럼 list[str]
    """

    return [
        col for col in column_names
        if col is not None
        and col is not NotImplemented
        and (not isinstance(col, str) or col.strip() != "")
        and col in df.columns
    ]


def drop_safely(
        df: pd.DataFrame,
        column_names: list[str],
        inplace: bool = True,
) -> pd.DataFrame:
    """
    DataFrame 에서 지정된 컬럼을 안전하게 삭제하고 반환

    inplace 기본 값은 True

    단, 전달된 column_names 내부의 특정 컬럼이 df 에 존재하지 않거나,
    정상적이지 않은 값 (None, NotImplemented, ' ', '') 이라도,
    별도의 에러 혹은 로그 처리 없이 무시

    :param df: 대상 pandas.DataFrame
    :param column_names: 삭제할 컬럼 목록 list[str]
    :param inplace: 기존 df 에 해당 메서드 로직 이후의 결과를 덮어쓸지 여부 bool
    :return: 지정 컬럼 삭제 후의 데이터 pandas.DataFrame
    """

    valid_drop_cols = get_valid_columns_in_df(df, column_names)

    if valid_drop_cols:
        df.drop(columns=valid_drop_cols, inplace=inplace)

    return df


def drop_invalid_columns_data_safely(
        df: pd.DataFrame,
        column_names: list[str],
        inplace: bool = True,
) -> pd.DataFrame:
    """
    DataFrame 에서 지정된 컬럼에 대해
    invalid 한 데이터를 가진 행을 안전하게 삭제하고 반환

    inplace 기본 값은 True

    단, 전달된 column_names 내부의 특정 컬럼이 df 에 존재하지 않거나,
    정상적이지 않은 값 (None, NotImplemented) 이라도,
    별도의 에러 혹은 로그 처리 없이 제외 후 반환

    동작 방식
    - 공백 (' ', '') 데이터 삭제
    - None/NaN/Null 데이터 삭제

    :param df: 대상 pandas.DataFrame
    :param column_names: 지정할 대상 컬럼 목록 list[str]
    :param inplace: 기존 df 에 해당 메서드 로직 이후의 결과를 덮어쓸지 여부 bool
    :return: 지정 컬럼 전처리 후의 데이터 pandas.DataFrame
    """

    valid_target_cols = get_valid_columns_in_df(df, column_names)

    if not valid_target_cols:
        return df

    # 계산용 전체 True 값인 series 생성
    valid_mask = pd.Series(True, index=df.index)

    # mask 에 누적 AND bool 연산하여, 개별 대상 컬럼들의 데이터가 모두 valid mask 를 만족하는 컬럼을 series 에 연산
    for column in valid_target_cols:
        series = df[column]

        # 유효 기준
        column_valid_mask = (
                series.notna()
                & series.astype("string").str.strip().ne("")
        )

        valid_mask &= column_valid_mask

    df.drop(index=df.index[~valid_mask], inplace=inplace)

    return df


def parse_number_columns_to_int_str_safely(
        df: pd.DataFrame,
        column_names: list[str],
        drop_invalid_rows: bool = True,
) -> pd.DataFrame:
    """
    DataFrame 에서 지정된 컬럼에 대해 int 변환 후 str 변환하여 반환

    반환된 DataFrame 을 기존 변수에 덮어쓸 필요 없이 inplace 처리

    이는 해당 숫자 데이터를 가진 컬럼에 대해 소수점/범위 처리를 위해 활용

    단, 전달된 column_names 내부의 특정 컬럼이 df 에 존재하지 않거나,
    정상적이지 않은 값 (None, NotImplemented) 이라도,
    별도의 에러 혹은 로그 처리 없이 무시

    특정 행 (row) 의 데이터에 int 로 변환할 수 없는 값 (ex. None, str...) 이 들어가 있다면
    drop_invalid_rows 값에 따라 해당 행을 제외 혹은 None 으로 남김

    :param df: 대상 pandas.DataFrame
    :param column_names: 지정할 대상 컬럼 목록 list[str]
    :param drop_invalid_rows: int 가 아닌 데이터 제거 여부 bool
    :return: 지정 컬럼 전처리 후의 데이터 pandas.DataFrame
    """

    valid_parse_cols = get_valid_columns_in_df(df, column_names)

    if not valid_parse_cols:
        return df

    parsed_rows = {}
    for col in valid_parse_cols:
        parsed_rows[col] = pd.to_numeric(df[col], errors="coerce")

    parsed_df = pd.DataFrame(parsed_rows)

    if drop_invalid_rows:
        df = df.loc[~parsed_df.isna().any(axis=1)].copy()
        parsed_df = parsed_df.loc[df.index]

    for col in valid_parse_cols:
        df[col] = (
            parsed_df[col]
            .astype("Int64")
            .astype(str)
            .replace("<NA>", None)
        )

    return df


def rename_safely(
        df: pd.DataFrame,
        column_name_mapping: dict[str, str],
) -> pd.DataFrame:
    """
    DataFrame 의 rename 에 대해
    rename 대상 columns dict 에서 key, value 중 None 인 값을 제외한 후
    안전하게 rename 및 반환

    :param df: 대상 pandas.DataFrame
    :param column_name_mapping: rename 매핑 정보를 가진 dict[str, str]
    :return: rename 전처리 후의 데이터 pandas.DataFrame
    """

    safe_columns = {}
    not_in_df_columns = []
    for key, value in column_name_mapping.items():
        if key is None or value in (None, NotImplemented):
            continue

        if key not in df.columns:
            not_in_df_columns.append(key)
            continue

        safe_columns[key] = value

    if not_in_df_columns:
        logging.warning(f"[FORMAT] process=rename_safely, missing_columns={not_in_df_columns}")

    return df.rename(columns=safe_columns, copy=True)


def reindex_safely(
        df: pd.DataFrame,
        column_names: list[str],
        is_strict: bool = False,
) -> pd.DataFrame:
    """
    DataFrame 의 reindex 에 대해
    reindex 대상 columns list 에서 value 중 None 혹은 잘못된 값 및 중복값을 제외한 후
    안전하게 reindex 및 반환

    :param df: 대상 pandas.DataFrame
    :param column_names: reindex 정보를 가진 list[str]
    :param is_strict: df 컬럼 목록과 column_names 정보가 완전히 일치하지 않으면 에러를 낼 것인지 여부 bool
    :return: reindex 전처리 후의 데이터 pandas.DataFrame
    """

    safe_columns = []
    not_in_df_columns = []
    invalid_type_columns = []

    for value in column_names:
        if value is None:
            continue

        if not isinstance(value, str):
            invalid_type_columns.append(value)
            continue

        if value not in df.columns:
            not_in_df_columns.append(value)
            continue

        safe_columns.append(value)

    # 중복 제거
    safe_columns = list(dict.fromkeys(safe_columns))

    # strict 여부
    if is_strict:
        error_messages = []

        if invalid_type_columns:
            error_messages.append(f"invalid_type_columns={invalid_type_columns}")

        if not_in_df_columns:
            error_messages.append(f"missing_columns={not_in_df_columns}")

        if set(column_names) != set(df.columns):
            error_messages.append(
                f"column_set_mismatch: expected={set(column_names)}, actual={set(df.columns)}"
            )

        if error_messages:
            raise ValueError(
                f"strict 한 reindex 과정에서 다음과 같은 이유로 에러가 발생했습니다. "
                f"코드 및 로그를 확인해주세요. : {error_messages}"
            )

    else:
        if not_in_df_columns:
            logging.debug(f"[FORMAT] process=reindex_safely, missing_columns={not_in_df_columns}")

        if invalid_type_columns:
            logging.debug(f"[FORMAT] process=reindex_safely, invalid_type_columns={invalid_type_columns}")

    return df.reindex(columns=safe_columns, copy=True)


def extract_flatten_format_from_nested_format(
        nested_format: Union[dict, list],
        key_delimiter: str = '.',
        value_delimiter: str = '',
        root_key_prefix: str = '',
) -> dict[str, str]:
    """
    nested format dict 데이터를 flatten format dict (일대일 구조) 으로 변환 후 반환

    해당 메서드는 nested 한 dict 형태의 데이터를 {key : value} 일대일 매핑하여 반환하며,
    주로 개별 데이터 (value) 에 개별 컬럼명 (key) 을 부여하기 위해 활용

    nested format 선언 규칙
    - value 는 str, dict, list 타입만 지원
    - list 의 경우 일반적인 {"key": ["one", "two"]} 형태로도 선언 가능하나,
      컬럼명 부여 등의 특수한 규칙을 적용할 경우 {"key": ["number"] * 2} 형태로도 선언 가능

    flatten format key 규칙 (key_delimiter="." 으로 가정)
    - str:
        "{outer_prefix}.{current_key}"
    - dict:
        "{outer_prefix}.{current_key}." 를 prefix 로 가지며, 재귀 실행
    - list:
        enumerate idx 에 따라 다음과 같이 진행
        - str: "{outer_prefix}.{list_key}.{idx}.{current_key}"
        - dict: "{outer_prefix}.{list_key}.{idx}.{current_key}." 를 prefix 로 가지며, 재귀 실행
        - list: "{list_key}.{outer_list_idx}.{inner_list_idx}." 를 prefix 로 가지며, 재귀 실행

    flatten format value 규칙 (key_delimiter=".", value_delimiter="" 으로 가정)
    - list:
        list 내의 모든 원소의 값이 모두 동일한 경우에 개별 원소 value 에 suffix 로 idx 가 부여됨

    주의 사항
    - list 내의 중복 dict 처리의 경우, 다음과 같은 상황에선 value 에 idx 자동 부여가 실행되지 못함
        - 혼합 자료형 (ex. ["str", {}, []])
        - 중첩 리스트 (ex. [[["val"]]*2]*3)

    사용 예시 (key_delimiter=".", value_delimiter="" 으로 가정)
    nested = {                                      flatten = {
        "str": "str_value",                             "str": "str_value"
        "dict": {                                       "dict.inner_dict": "inner_value"
            "inner_dict": "inner_value"                 "list.1" = "list_value1"
        },                                              "list.2" = "list_value2"
        "list": ["list_value"] * 3                      "list.3" = "list_value3"
    }                                               }

    :param nested_format: nested format dict[str, Any]
    :param key_delimiter: 재귀 및 idx 에서 key 규칙에 추가될 구분자 str
    :param value_delimiter: 재귀 및 idx 에서 value 규칙에 추가될 구분자 str
    :param root_key_prefix: 모든 key 의 가장 앞에 붙을 prefix str
    :return: 일대일 매핑된 flatten format dict[str, str]
    """

    if nested_format is None or not isinstance(nested_format, (list, dict)):
        logging.debug(f"[FORMAT] process=extract_flatten_format_from_nested_format, parameter={nested_format}: "
                      f"Invalid value in parameter")
        return {}

    def _flatten(
            data: Any,
            key_prefix: str = '',
            _key_delimiter: str = '.',
            _value_delimiter: str = '',
    ):
        if isinstance(data, str):
            flat[key_prefix] = data
            return

        if isinstance(data, dict):
            for key, value in data.items():
                current_key_prefix = f"{key_prefix}{_key_delimiter}{key}" if key_prefix else key
                _flatten(
                    data=value,
                    key_prefix=current_key_prefix,
                    _key_delimiter=_key_delimiter,
                    _value_delimiter=_value_delimiter,
                )
            return

        if isinstance(data, list):
            # 리스트 내 원소의 값 (주소가 아닌 실제 value, 컬럼명) 이 모두 같은지 확인 (dict, list, str 포함)
            try:
                is_all_same = len({json.dumps(x, sort_keys=True) for x in data}) == 1
            except TypeError:
                is_all_same = False

            for idx, item in enumerate(data, start=1):
                current_key = build_indexed_column_name(key_prefix, idx, _key_delimiter)

                # str
                if isinstance(item, str):
                    # 같은 문자열 반복일 시 index 추가
                    if is_all_same:
                        flat[current_key] = build_indexed_column_name(item, idx, _value_delimiter)
                    else:
                        flat[current_key] = item
                    continue

                # dict
                if isinstance(item, dict):
                    # 같은 dict 반복일 시 내부 value 에 index 추가 (재귀)
                    if is_all_same:
                        indexed_dict = {
                            k: f"{v}{_value_delimiter}{idx}" if isinstance(v, str) else v
                            for k, v in item.items()
                        }
                        _flatten(
                            data=indexed_dict,
                            key_prefix=current_key,
                            _key_delimiter=_key_delimiter,
                            _value_delimiter=_value_delimiter,
                        )
                    else:
                        _flatten(
                            data=item,
                            key_prefix=current_key,
                            _key_delimiter=_key_delimiter,
                            _value_delimiter=_value_delimiter,
                        )
                    continue

                # list
                if isinstance(item, list):
                    # 중첩 list 일 시 재귀 수행
                    _flatten(
                        data=item,
                        key_prefix=current_key,
                        _key_delimiter=_key_delimiter,
                        _value_delimiter=_value_delimiter,
                    )
                    continue

                # Unsupported type
                logging.debug(
                    f"[FORMAT] target_key={current_key}, target_data_type={type(item)}, target_data:{item}: "
                    f"Unsupported type"
                )
                continue

            return

        # Unsupported type
        logging.debug(
            f"[FORMAT] target_key={key_prefix}, target_data_type={type(data)}, target_data:{data}: "
            f"Unsupported type"
        )
        return

    flat = {}
    _flatten(
        data=nested_format,
        key_prefix=root_key_prefix,
        _key_delimiter=key_delimiter,
        _value_delimiter=value_delimiter,
    )

    return flat


def filter_dataframe(
        df: pd.DataFrame,
        filters: dict = None,
        allow_wildcard: bool = True,
) -> pd.DataFrame:
    """
    DataFrame 을 특정 조건에 의해 필터링 하고 반환

    파라미터로 받은 filters (dict) 를 조건으로 취급,
    key 와 일치하는 DataFrame 의 column 에서,
    value 와 완전 일치 or 부분 일치 하는 데이터들만을 추출하고 DataFrame 으로 반환

    이때, 완전 일치 or 부분 일치 여부는 allow_wildcard 의 여부에 따라 달라지며,
    True (기본값) 의 경우 부분 일치, False 의 경우 완전 일치 조건이 됨
    (완전 일치/부분 일치 모두 대소문자를 구분하지 않음)

    :param df: 필터링 대상 데이터 pandas.DataFrame
    :param filters: {column 명 - 완전 일치/부분 일치 문자열} 쌍의 추출 조건 dict
    :param allow_wildcard: 추출 조건의 완전 일치 or 부분 일치 여부 bool (기본값 부분 일치)
    :return: 필터링 후의 pandas.DataFrame
    """

    if not filters:
        return df.copy()

    # 컬럼명 전부 소문자로 변환
    df_lower = df.copy()
    df_lower.columns = [col.lower() for col in df_lower.columns]

    # 필터 조건도 소문자로 변환
    filters_lower = {k.lower(): str(v).lower() for k, v in filters.items()}

    filtered_df = df_lower.copy()

    for col, val in filters_lower.items():
        if col not in filtered_df.columns:
            logging.warning(f"[SKIP] process=filter_dataframe, target_filter={col}: "
                            f"Not found target filter in target dataframe")
            continue

        # 비교할 대상 컬럼도 문자열 소문자로 변환
        row_lower = filtered_df[col].astype(str).str.lower()

        if allow_wildcard:
            # 부분 일치 (포함 여부)
            row_result = row_lower.str.contains(val, na=False)
        else:
            # 완전 일치
            row_result = row_lower == val

        filtered_df = filtered_df[row_result]

    return filtered_df


def build_indexed_column_name(
        column_name: str,
        index: int,
        delimiter: str = '',
) -> str:
    """
    공통 인덱스 컬럼 규칙 정의 및 반환

    :param column_name: 인덱스를 적용할 컬럼명 str
    :param index: 인덱스 번호 int
    :param delimiter: 인덱스와 컬럼명 사이에 들어갈 구분자 str
    :return: 공통 인덱스 컬럼 규칙을 적용한 컬럼명 str
    """

    return f"{column_name}{delimiter}{index}"


def validate_required_columns_in_df(
        df: pd.DataFrame,
        column_names: list[str],
) -> None:
    """
    검증 대상 df 컬럼 목록에 required columns 원소가 전부 존재하는지 검증

    :param df: 검증 대상 pandas.DataFrame
    :param column_names: 필수 컬럼 목록 list[str]
    :return: 없음
    """

    column_names = set(column_names)
    df_columns = set(df.columns)

    missing_columns = column_names - df_columns

    if missing_columns:
        raise ValueError(
            f"검증 대상 df 의 컬럼 목록 {df_columns} 에서, 필수 컬럼 {missing_columns} 이/가 존재하지 않습니다. 코드를 확인해주세요."
        )
