"""
logging_util.py
----------------

로그 처리 및 로그 데이터 관련 util 모듈
"""


import functools
import logging
import time
import uuid
from pathlib import Path
from typing import Union, Literal, Callable, Optional

import pandas as pd

from util.path_util import get_file_name_by_path


def run_with_logging(log_metadata: Union[dict, Callable] = None) -> Callable:
    """
    반복되는 프로세스 (메서드) 의 시작/끝 구분 로그를 위한 데코레이터 패턴
    로그 목적 로그 파라미터를 받기 위해 데코레이터 팩토리로 구현

    주의 사항
    - 로그에 추가적인 log_metadata 가 필요하지 않더라도
      @run_with_logging() 처럼 선언하여야 에러가 발생하지 않음

    :param log_metadata: 로그에 추가할 metadata 관련 Union[dict, Callable]
    :return: 데코레이터 패턴용 method Callable
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            func_full_name = f"{func.__module__}.{func.__qualname__}"

            # dict / callable 처리
            metadata = None
            if callable(log_metadata):
                metadata = log_metadata(*args, **kwargs)
            elif isinstance(log_metadata, dict):
                metadata = log_metadata

            # 메타 데이터 관련 처리
            metadata_str = ""
            if metadata:
                kv_pairs = [f"{k}={v}" for k, v in metadata.items()]
                metadata_str = ", " + ", ".join(kv_pairs)

            # 해당 프로세스에 부여할 job id 생성
            job_id = str(uuid.uuid4())[:8]

            logging.info(f"[BEGIN] job_id={job_id}, process={func_full_name}{metadata_str}: Started")
            start_time = time.time()

            # 프로세스 성공 여부에 따라 로그 분기 처리
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                logging.info(f"[SUCCESS] job_id={job_id}, process={func_full_name}{metadata_str}: "
                             f"Completed ({elapsed:.2f}s)")
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logging_error_event(
                    log_prefix="FAILED",
                    log_level="exception",
                    exception_instance=e,
                    log_metadata={
                        "job_id": job_id,
                        "process": func_full_name, **(metadata or {})
                    },
                    log_message=f"Failed (elapsed={elapsed:.2f}s): {e}"
                )
                raise
        return wrapper
    return decorator


def logging_file_event(
        file_path: Union[Path, str],
        log_prefix: Literal["LOAD", "SAVE", "DELETE"],
        log_metadata: Optional[dict] = None,
        df: Optional[pd.DataFrame] = None,
        log_message: Optional[str] = None,
        log_level: Literal["info", "debug", "warning", "error", "critical", "exception"] = "info",
) -> None:
    """
    반복되는 파일 save/load 성공 여부 로그를 위한 로그 출력 전용 메서드

    :param file_path: 대상 파일 경로 Union[Path, str]
    :param log_prefix: 파일 처리 종류 Literal["LOAD", "SAVE", "DELETE"]
    :param log_metadata: 추가 로그 정보 Optional[dict]
    :param df: 파일 처리 대상 Optional[pd.DataFrame]
    :param log_message: 로그 메세지 Optional[str]
    :param log_level: 로그 레벨 Literal["info", "debug", "warning", "error", "critical", "exception"]
    :return: 없음
    """

    # 로그 메타 데이터 부 설정 및 통합
    log_metadatas = []

    log_metadatas.append(f"target_name={get_file_name_by_path(file_path)}")

    if df is not None:
        rows, cols = df.shape
        log_metadatas.append(f"rows={rows}")
        log_metadatas.append(f"cols={cols}")

    if log_metadata:
        log_metadatas.extend(f"{k}={v}" for k, v in log_metadata.items())

    log_metadatas.append(f"path={file_path}")

    # 로그 메세지 부 설정
    if not log_message or not log_message.strip():
        log_message = ""
    else:
        log_message = f": {log_message}"

    # 전체 로그 통합
    full_log = f"[{log_prefix}] {', '.join(log_metadatas)}{log_message}"
    getattr(logging, log_level)(full_log)


def logging_error_event(
        exception_instance: Optional[Exception] = None,
        log_message: str = "",
        log_message_detail: str = "",
        log_metadata: Optional[Union[dict, str]] = None,
        log_prefix: str = "ERROR",
        log_level: Literal["error", "critical", "exception"] = "error",
) -> None:
    """
    반복되는 에러 로그를 위한 로그 출력 전용 메서드

    :param exception_instance: 대상 에러 인스턴스 Optional[Exception]
    :param log_message: 에러 로그 메세지 str
    :param log_message_detail: 추가 에러 로그 메세지 (에러 인스턴스 string representation) str
    :param log_metadata: 추가 에러 로그 정보 Optional[Union[dict, str]]
    :param log_prefix: 에러 종류 str
    :param log_level: 로그 레벨 Literal["error", "critical", "exception"]
    :return: 없음
    """

    # 전체 로그 설정 및 통합
    full_log = f"[{log_prefix}] "

    # 로그 메타 데이터 부 설정 및 통합
    log_metadatas = []
    if exception_instance:
        log_metadatas.append(f"error={type(exception_instance).__name__}")

    if log_metadata:
        if isinstance(log_metadata, dict):
            log_metadatas.extend(f"{k}={v}" for k, v in log_metadata.items())
        elif isinstance(log_metadata, str) and log_metadata.strip():
            log_metadatas.append(log_metadata)

    if log_metadatas:
        full_log += ", ".join(log_metadatas)

    # 로그 메세지 부 설정 및 통합
    if log_message:
        if log_metadatas:
            full_log += ": "
        full_log += log_message

    if log_message_detail:
        if log_metadatas:
            if log_message:
                full_log += " - "
            else:
                full_log += ": "
        full_log += log_message_detail

    getattr(logging, log_level)(full_log)


def extract_log_info(
    method: str,
    params: Optional[dict] = None,
    payload: Optional[dict] = None,
    log_type: Optional[Literal["params", "payload"]] = None,
    log_keys: Optional[list] = None,
) -> str:
    """
    API 의 query params 혹은 payload 데이터에서 특정 key 의 값만을 추출하기 위한 메서드
    로그 메타 데이터 수집 목적으로 활용

    :param method: 대상 API method str
    :param params: 대상 API query parameters Optional[dict]
    :param payload: 대상 API payload Optional[dict]
    :param log_type: 대상 API 에서의 데이터 수집 위지 Optional[Literal["params", "payload"]]
    :param log_keys: 수집할 데이터의 key Optional[list]
    :return: 추출, 수집, 통합 및 포맷팅 된 전체 로그 str
    """

    # log_type 이 None 이면 method 기준 자동 결정
    if log_type is None:
        log_type = "params" if method.upper() == "GET" else "payload"

    # params 또는 payload 결정 (params 가 명시 되지 않으면 payload 기준)
    source = params if log_type == "params" else payload

    # source 나 log_keys 가 비어 있으면 빈 문자열 return
    if not source or not log_keys:
        return ""

    # 지정한 key 가 source 에 있으면 "key=value" 형식 (로그 컨벤션) 문자열 return
    values = [f"{k}={source[k]}" for k in log_keys if k in source]
    return ", ".join(values)
