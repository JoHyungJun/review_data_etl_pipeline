"""
excel_util.py
-------------

Excel 의 포맷팅/삽입/삭제/연산 관련 util 모듈
"""
import io
import logging
import re
from pathlib import Path
from typing import Union, Optional, BinaryIO

import pandas as pd
import numpy as np
from natsort import natsorted

from core.implementation.storage.excel.spec.excel_load_spec import ExcelLoadSpec
from core.implementation.storage.excel.storage.excel_storage import ExcelStorage
from util.column_util import parse_number_columns_to_int_str_safely

from util.logging_util import logging_file_event, logging_error_event
from util.path_util import get_file_name_by_path


def get_sheet_name_safely(raw_sheet_name: str) -> str:
    """
    Excel 시트명 문법에 맞게 변환 후 반환

    Excel 시트명 설정 규칙
    - 시트명에 사용할 수 없는 특정 특수 문자는 '_' 으로 변환
    - 빈 시트명은 "Unknown_Sheet" 으로 설정
    - 시트명 최대 길이인 31 글자까지만 허용

    :param raw_sheet_name: 처리 대상 시트명
    :return: 전처리 후의 시트명 str
    """

    sanitized_sheet_name = re.sub(r'[:\\/*?\[\]]', '_', raw_sheet_name).strip()

    if not sanitized_sheet_name:
        sanitized_sheet_name = "Unknown_Sheet"

    return sanitized_sheet_name[:31]


def get_all_excel_files_from_directory(directory_path: Path) -> list[Path]:
    """
    특정 directory path 의 모든 Excel 에 대하여 Path 목록을 반환

    - directory path 존재 여부 검증
    - path 가 directory path 가 맞는지 여부 검증

    :param directory_path: 전체 Excel 을 가져올 대상 directory path
    :return: 해당 directory path 에 존재하는 개별 Excel 경로 list[Path]
    """

    if not directory_path.exists():
        raise FileNotFoundError(f"존재하지 않는 디렉토리 경로입니다. 경로를 확인해주세요. : {directory_path}")

    if not directory_path.is_dir():
        raise NotADirectoryError(f"해당 경로는 디렉토리가 아닙니다. 경로를 확인해주세요. : {directory_path}")

    return natsorted([file for file in directory_path.iterdir() if file.suffix.lower() == ".xlsx"])


def merge_target_excel_columns_from_directory(
        directory_path: Union[str, Path],
        target_headers: list[str],
        output_file_path: Union[str, Path]
) -> Optional[pd.DataFrame]:
    """
    특정 directory path 의 모든 Excel 에 대하여
    target_headers 컬럼만 추출하여 하나의 DataFrame 으로 합치고, 하나의 Excel 로 통합하여 save

    :param directory_path: 전체 Excel 을 가져올 대상 directory path
    :param target_headers: 추출 대상 컬럼명 list
    :param output_file_path: 최종 산출물 Excel save 경로
    :return: 결과 Optional[pandas.DataFrame] (에러 발생 혹은 결과 데이터 없을 시 None 반환)
    """

    directory_path = Path(directory_path)
    output_file_path = Path(output_file_path)

    try:
        excel_files = get_all_excel_files_from_directory(directory_path)
        logging_file_event(
            log_prefix="LOAD",
            file_path=directory_path,
            log_metadata={
                "target_directory_path": directory_path,
                "excel_files_count": len(excel_files),
            },
        )
    except Exception as e:
        logging_error_event(
            exception_instance=e,
            log_metadata={
                "target_directory_path": directory_path,
            },
            log_message="While loading excel files from target directory",
            log_message_detail=str(e)
        )
        return None

    # 해당 디렉토리에 존재하는 Excel 들을 순회하며 로직 처리
    merged_df = pd.DataFrame()
    for file_path in excel_files:
        try:
            df = pd.read_excel(file_path, dtype=str)
            logging_file_event(
                log_prefix="LOAD",
                file_path=file_path,
                df=df,
            )
        except Exception as e:
            logging_error_event(
                exception_instance=e,
                log_metadata={"target_file_path": file_path},
                log_message="While reading excel file",
                log_message_detail=str(e)
            )
            continue

        # 해당 Excel 파일에 존재하지 않는 헤더 로그 처리
        missing_headers = [h for h in target_headers if h not in df.columns]
        if missing_headers:
            logging.warning(
                f"[SKIP] target_file_name={file_path.name}, missing_target_headers={missing_headers}: "
                "Not found target headers"
            )

        # 존재하는 컬럼만 추출 및 통합
        existing_headers = [h for h in target_headers if h in df.columns]
        if existing_headers:
            merged_df = pd.concat([merged_df, df[existing_headers]], ignore_index=True)
            logging.info(f"[MERGE] target_file={get_file_name_by_path(file_path)}")

    if merged_df.empty:
        logging.warning(f"[STOP] target_directory_path={directory_path}: Not found any valid target headers")
        return None

    try:
        merged_df.to_excel(output_file_path, index=False)
        logging_file_event(
            log_prefix="SAVE",
            file_path=output_file_path,
            df=merged_df,
        )
    except Exception as e:
        logging_error_event(
            exception_instance=e,
            log_metadata={"output_file_path": output_file_path},
            log_message="While save excel file",
            log_message_detail=str(e)
        )

    return merged_df


def normalize_dataframe_types_strict(
        df: pd.DataFrame,
        column_names: Optional[list[str]] = None,
) -> pd.DataFrame:
    """
    df 의 개별 컬럼의 컬럼 타입을 단일화 후 반환

    df 의 개별 컬럼 데이터들이 여러 타입을 가지고 있을 때
    duck db 를 이용한 save/load 에서 에러가 나는 것을 방어하기 위해 df 의 컬럼 타입을 단일화
    
    주의 사항
    - Excel 에서 load 한 df 의 경우, None (NaN) 값은 float64 타입으로 명시됨
    - column_names 가 None 인 경우, 모든 컬럼에 대해 타입 단일화를 진행

    :param df: 컬럼 타입 단일화 대상 pandas.DataFrame
    :param column_names: 단일화 대상 컬럼 목록 Optional[list[str]]
    :return: 컬럼 타입 단일화 된 pandas.DataFrame
    """

    df = df.copy()

    if not column_names:
        target_columns = list(df.columns)
    else:
        target_columns = [col for col in column_names if col in df.columns]

    for column in target_columns:
        series = df[column]

        # NaN 을 제외한 전체 컬럼 값
        non_null = series.dropna()

        # 해당 컬럼에 NaN 값밖에 없었다면 전체 str 처리
        if non_null.empty:
            df[column] = series.astype("string")
            continue

        # NaN 이 아닌 값들을 데이터 타입만 추출하여 set 처리
        types = set(map(type, non_null))

        # nested type (list, dict) 값을 가지고 있었다면 전체 str 처리
        if any(t in (list, dict) for t in types):
            df[column] = series.astype("string")
            continue

        # str 타입을 가지고 있었다면 안전하게 전체 값을 str 처리
        if str in types:
            df[column] = series.astype("string")
            continue

        # str 이 아닌 numeric 타입을 가지고 있었다면 중요도에 따라 처리
        if all(issubclass(t, (int, float, np.integer, np.floating)) for t in types):
            has_nan = series.isna().any()

            numeric_series = pd.to_numeric(series, errors="coerce")

            has_float = ((numeric_series % 1) != 0).any()

            # float 값이 하나라도 있으면 전체 값을 float 처리
            if has_float:
                df[column] = numeric_series.astype("float64")
            else:
                # float 값이 하나도 없고 NaN 값이 있다면 nullable int 처리
                if has_nan:
                    df[column] = numeric_series.astype("Int64")
                # float 값이 하나도 없고 NaN 값도 없다면 int 처리
                else:
                    df[column] = numeric_series.astype("int64")

            continue

        # 모든 분기에 해당하지 않는 타입은 str 처리
        df[column] = series.astype("string")

    return df


def get_excel_binary_from_dataframe(df: pd.DataFrame) -> BinaryIO:
    """
    df 를 binary 형태의 excel 파일로 반환

    :param df: 변환 대상 pandas.DataFrame
    :return: 변환된 df BinaryIO
    """

    excel_buffer = io.BytesIO()

    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)

    excel_buffer.seek(0)

    return excel_buffer


def extract_review_ids_from_excel(
        storage: ExcelStorage,
        load_spec: ExcelLoadSpec,
        review_id_column_name: str,
) -> list[int]:
    """
    Excel 의 id 컬럼 전체 데이터만 추출하여 반환

    :param storage: Excel save/load 로직을 가진 ExcelStorage
    :param load_spec: load 관련 세부 정보 설정값을 가진 ExcelLoadSpec
    :param review_id_column_name: 추출 대상 Excel 의 리뷰 id 관련 컬럼명 str
    :return: 검증 및 파싱 완료된 id list[int]
    """

    df = storage.load(load_spec)
    df = parse_number_columns_to_int_str_safely(
        df=df,
        column_names=[review_id_column_name],
        drop_invalid_rows=True,
    )

    if review_id_column_name not in df.columns:
        return []

    return list(
        dict.fromkeys(
            int(review_id)
            for review_id in df[review_id_column_name].dropna()
        )
    )
