"""
review_id_hashing.py
--------------------

플랫폼에서 수집한 리뷰 id 에 새롭게 해싱된 리뷰 id 를 부여하는 모듈

여러 플랫폼에서 수집한 리뷰 데이터들이 혼재하므로
개별 플랫폼에서 부여된 리뷰 id 를 재활용 할 시엔 충돌 위험 존재

따라서 리뷰 작성 날짜/시간 데이터 + SHA256 으로 해싱된 리뷰 id 값을 활용하여
새로운 리뷰 id 값을 df 개별 행 (레코드) 별로 만들고, 기존 리뷰 id 값 대체

post processing 중 한 단계의 모듈 (Optional)
"""


import logging
from datetime import datetime
from typing import Optional
import pandas as pd
import hashlib

from domain.platform.platform import Platform
from util.column_util import (
    validate_required_columns_in_df,
    drop_invalid_columns_data_safely,
    reindex_safely,
)
from util.datetime_util import safe_parse_timestamp
from util.logging_util import run_with_logging


@run_with_logging(
    lambda *args, **kwargs: (
        {"platform": kwargs["platform"].get_platform_eng_name()}
        if kwargs.get("platform") is not None
        else {}
    )
)
def review_id_hashing(
        platform: Optional[Platform],
        df: pd.DataFrame,
        review_id_column: str,
        review_created_date_column: str,
        review_created_time_column: str,
        hashed_review_id_length: int,
) -> pd.DataFrame:
    """
    리뷰 id 해싱 정보 및 리뷰 작성 날짜/시간 정보를 기반으로 기존 리뷰 id 값 대체
    
    df 에서 필수 컬럼별 series (열) 단위로 추출한 후 로직 적용

    해싱 규칙 (YYYYmmddHHMM + 1~4 자리 사이의 해싱된 리뷰 id)
    - 해싱된 리뷰 id 는 최소 13, 최대 16 자리 (VReview export 규칙 상 최대 16 자리)
    - 앞 8자리는 리뷰 작성 날짜 (YYYYmmdd)
    - 다음 4자리는 리뷰 작성 시각, 분 (HHMM)
    - 마지막 1~4자리는 원 리뷰 id 를 sha256 해싱 후, 문자열을 숫자로 16 진수 변환하여, 자릿수만큼 mod

    주의 사항
    - 로직에 사용되는 필수 컬럼이 공백 혹은 None/NaN/Null 등 invalid 한 데이터일 경우, 해당 레코드는 제거됨

    :param platform: 리뷰 id 해싱 대상 데이터의 플랫폼 정보 Optional[Platform]
                     (로그 처리를 위한 인자이며, 반드시 keyword argument 방식으로 인자를 넘겨야 함)
    :param df: 보정 대상 pandas.DataFrame
    :param review_id_column: 보정 대상 df 의 리뷰 id 관련 컬럼명 str
    :param review_created_date_column: 보정 대상 df 의 리뷰 작성 날짜 관련 컬럼명 str
    :param review_created_time_column: 보정 대상 df 의 리뷰 작성 시간 관련 컬럼명 str
    :param hashed_review_id_length: 해싱 이후 리뷰 id 의 길이
    :return: 보정된 pandas.DataFrame
    """

    input_df_len = len(df)
    ordered_column_names = list(df.columns)

    df = df.copy()

    # 필수 컬럼 검증
    required_columns = [
        review_id_column,
        review_created_date_column,
        review_created_time_column,
    ]

    validate_required_columns_in_df(
        df=df,
        column_names=required_columns,
    )

    drop_invalid_columns_data_safely(
        df=df,
        column_names=required_columns,
    )

    # 해싱 규칙에 따른 해싱 아이디 길이 검증
    MAX_HASH_LENGTH = 16
    MIN_HASH_LENGTH = 13

    if not (MIN_HASH_LENGTH <= hashed_review_id_length <= MAX_HASH_LENGTH):
        raise ValueError(
            f"해싱 이후 리뷰 id 는 최소 {MIN_HASH_LENGTH}, 최대 {MAX_HASH_LENGTH} "
            f"자리가 보장되어야 합니다. "
            f"해싱 길이 값 (hashed_review_id_length) 을 수정하거나 해싱 규칙을 확인해주세요."
        )

    # datetime parsing
    # 원본 컬럼의 포맷 변경 없이 임시 series 로 처리
    parsed_date_series = df[review_created_date_column].apply(safe_parse_timestamp)
    parsed_time_series = df[review_created_time_column].apply(safe_parse_timestamp)

    # 유효 기준
    valid_mask = (
        df[review_id_column].notna()
        & parsed_date_series.notna()
        & parsed_time_series.notna()
    )

    invalid_row_count = (~valid_mask).sum()

    if invalid_row_count > 0:
        logging.warning(
            f"[DELETE] invalid_review_rows_removed={invalid_row_count}: "
            f"Found invalid format rows while review id hashing"
        )

    # invalid row 제거
    df = df.loc[valid_mask].copy()

    # 추출한 series 에도 동일 유효 기준 적용
    parsed_date_series = parsed_date_series.loc[valid_mask]
    parsed_time_series = parsed_time_series.loc[valid_mask]

    # 날짜/시간 formatting
    date_format = "%Y%m%d"
    date_str_series = parsed_date_series.dt.strftime(date_format)

    time_format = "%H%M"
    time_str_series = parsed_time_series.dt.strftime(time_format)

    datetime_str_series = date_str_series + time_str_series

    # hashing 기준이 되는 리뷰 id 길이 계산
    dummy_datetime = datetime(1995, 9, 12, 0, 0)
    date_len = len(dummy_datetime.strftime(date_format))  # 8
    time_len = len(dummy_datetime.strftime(time_format))  # 4

    review_id_hash_length = hashed_review_id_length - (date_len + time_len)

    # 리뷰 id hashing
    hashed_review_id_series = df[review_id_column].astype(str).apply(
        lambda review_id: str(
            int(
                hashlib.sha256(review_id.encode()).hexdigest(),
                16,
            ) % (10 ** review_id_hash_length)
        ).zfill(review_id_hash_length)
    )

    # 보정
    df[review_id_column] = datetime_str_series + hashed_review_id_series

    # 중복 id 검사 및 로그 처리
    duplicated_count = df[review_id_column].duplicated(keep=False).sum()
    duplicated_review_ids = (
        df[df[review_id_column].duplicated(keep=False)][review_id_column]
        .unique()
        .tolist()
    )

    if duplicated_count > 0:
        logging.warning(f"[WARN] duplicated_review_id_count={duplicated_count}, "
                        f"duplicated_review_ids={duplicated_review_ids[:10]}: "
                        f"Found duplicated review id after review id hashing")

    logging.info(f"[END] prev_df_len={input_df_len}, processed_df_len={len(df)}")

    df = reindex_safely(
        df=df,
        column_names=ordered_column_names,
        is_strict=True,
    )
    return df
