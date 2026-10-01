"""
api_util.py
-----------

API request/response 및 API 데이터 포맷팅/처리 관련 util 모듈
"""


import logging
import time
import requests
from typing import Optional, Literal
from urllib.parse import urlencode
from fastapi import status

from error.api import ExternalScrapingApiAuthenticationExpiredError
from util.logging_util import extract_log_info, logging_error_event


def get_encoded_url(base_url: str, params: dict) -> str:
    """
    기본 문자열 URL 을 인코딩하여 반환

    :param base_url: URL 기본 경로 str
    :param params: URL query parameters dict
    :return: 인코딩된 최종 URL str
    """

    new_params = []

    # 전체 URL 로 통합
    for k, v in params.items():
        if isinstance(v, list):
            for item in v:
                new_params.append((k, item))
        else:
            new_params.append((k, v))

    return f"{base_url}?{urlencode(new_params)}"


def get_response_safely_with_retries(
        method: str,
        base_url: str,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
        payload: Optional[dict] = None,
        files: Optional[dict] = None,
        max_retries: int = 3,
        delay_seconds: float = 1.0,
        log_type: Optional[Literal["params", "payload"]] = None,
        log_keys: Optional[list] = None,
) -> Optional[requests.Response]:
    """
    API request 의 안정성을 위해 성공적인 데이터 응답의 response 까지
    최대 설정된 횟수 (max_retries) 만큼  API request 를 시도하고,
    로그 처리 및 response 데이터 반환

    :param method: HTTP method str
    :param base_url: URL 기본 경로 str
    :param params: URL query parameters Optional[dict]
    :param headers: headers Optional[dict]
    :param payload: body (json) Optional[dict]
    :param files: 전송할 files Optional[dict]
    :param max_retries: 최대 재시도 횟수 int
    :param delay_seconds: 재시도 간격 (초 단위) float
    :param log_type: 로그 추출 대상 type Optional[Literal["params", "payload"]]
    :param log_keys: 로그 추출 대상 데이터의 key Optional[list]
    :return: request 성공 여부에 따른 Optional[requests.Response]
    """

    # 로그 데이터 추출
    log_metadata = extract_log_info(
        method=method,
        params=params,
        payload=payload,
        log_type=log_type,
        log_keys=log_keys,
    ) or ""

    # 성공적인 response 데이터 응답까지 max_retries 만큼 API request 시도
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.request(
                method=method,
                url=base_url,
                params=params,
                headers=headers,
                json=payload,
                files=files,
            )
            return response
        except requests.RequestException as e:
            logging.warning(f"[RETRY] {log_metadata + ': ' if log_metadata else ''}attempt=[{attempt}/{max_retries}] "
                            f"Request error - {e}")

            # 과도한 API 요청 방지를 위한 재시도 간격 (delay_seconds) 만큼 request 휴식
            if attempt < max_retries:
                time.sleep(delay_seconds)

    # 최대 횟수 (max_retries) 모두 실패 시 로그 처리 및 None 반환
    logging_error_event(
        log_prefix="STOP",
        log_metadata=log_metadata,
        log_message=f"All {max_retries} attempts failed"
    )
    return None


def get_expected_status_response_safely_with_retries(
        method: str,
        base_url: str,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
        payload: Optional[dict] = None,
        files: Optional[dict] = None,
        expected_status_codes: Optional[set] = None,
        max_retries: int = 3,
        delay_seconds: float = 1.0,
        log_type: Optional[Literal["params", "payload"]] = None,
        log_keys: Optional[list] = None,
) -> Optional[requests.Response]:
    """
    API request 의 안정성을 위해 성공적인 데이터/상태 코드 응답의 response 까지
    최대 설정된 횟수 (max_retries) 만큼  API request 를 시도하고,
    로그 처리 및 response 데이터 반환

    주의 사항
    - 해당 메서드는 외부 API 통신을 담당하므로,
      에러 발생 시 애플리케이션 내부 규약에 따라 일부 특정 에러 response 를 커스텀 에러로 raise 함


    :param method: HTTP method str
    :param base_url: URL 기본 경로 str
    :param params: URL query parameters Optional[dict]
    :param headers: headers Optional[dict]
    :param payload: body (json) Optional[dict]
    :param files: 전송할 files Optional[dict]
    :param expected_status_codes: 상태 코드 기댓값 Optional[set]
    :param max_retries: 최대 재시도 횟수 int
    :param delay_seconds: 재시도 간격 (초 단위) float
    :param log_type: 로그 추출 대상 type Optional[Literal["params", "payload"]]
    :param log_keys: 로그 추출 대상 데이터의 key Optional[list]
    :return: request 성공 여부에 따른 Optional[requests.Response]
    """

    # 기본값 부여
    if not expected_status_codes:
        expected_status_codes = {200}

    # 로그 데이터 추출
    log_metadata = extract_log_info(
        method=method,
        params=params,
        payload=payload,
        log_type=log_type,
        log_keys=log_keys,
    ) or ""

    # 성공적인 response 데이터/상태 코드 응답까지 max_retries 만큼 API request 시도
    response = None
    for attempt in range(1, max_retries + 1):
        response = get_response_safely_with_retries(
            method=method,
            base_url=base_url,
            params=params,
            headers=headers,
            payload=payload,
            files=files,
            max_retries=1,
            delay_seconds=delay_seconds,
        )

        # success
        if response is not None:
            if response.status_code in expected_status_codes:
                logging.debug(f"[SUCCESS] {log_metadata + ', ' if log_metadata else ''}"
                              f"status={response.status_code}, base_url={base_url}: API response")
                return response

        # failed
        if response is not None:
            logging.warning(
                f"[FAILED] {log_metadata + ', ' if log_metadata else ''}"
                f"status={response.status_code}, base_url={base_url}: "
                f"[{attempt}/{max_retries}] Response failed - {response.text}"
            )
        else:
            logging.warning(
                f"[FAILED] {log_metadata + ', ' if log_metadata else ''}"
                f"[{attempt}/{max_retries}] Response failed - No response"
            )

        # 과도한 API 요청 방지를 위한 재시도 간격 (delay_seconds) 만큼 request 휴식
        if attempt < max_retries:
            time.sleep(delay_seconds)

    # 특정 에러 status code 의 경우 raise
    if response is not None:
        if response.status_code == status.HTTP_401_UNAUTHORIZED:
            raise ExternalScrapingApiAuthenticationExpiredError(
                "API 토큰이 만료되었습니다. 외부 설정값을 확인해주세요."
            )

    # 최대 횟수 (max_retries) 모두 실패 시 로그 처리 및 None 반환
    logging_error_event(
        log_prefix="FAIL",
        log_metadata=log_metadata,
        log_message=f"Failed after {max_retries} attempts"
    )
    return None


def get_snos_hash(snos: list[int]) -> int:
    """
    sno List 를 해싱하여 하나의 고유 key (해당 List 의 pk) 생성

    :param snos: sno list[int]
    :return: sno List 를 해싱한 고유 식별자 key (pk) int
    """

    # 중복 제거 및 정렬 후 문자열로 변환하여 해시 생성
    return hash(str(sorted(frozenset(snos))))


def is_duplicate_snos(snos: list[int], seen_sno_hashes: set[int]) -> bool:
    """
    해당 sno list (snos) 를 해싱하고
    해당 해싱 값이 이전에 수집 되었던 해싱된 sno list 의 모음 (seen_sno_hashes) 중 하나와 중복되는지 검증

    :param snos: 현재 확인할 list[int]
    :param seen_sno_hashes: 이미 확인된 sno set[int]
    :return: 존재 (중복) 여부 bool
    """

    # 현재 sno 리스트 해시 값이 seen_hashes 에 존재하는지 확인
    return get_snos_hash(snos) in seen_sno_hashes
