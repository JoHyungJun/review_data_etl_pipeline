"""
order_history_scraping.py
-------------------------

플랫폼별 API 를 통한 주문 내역 데이터 수집 및 저장 모듈

주요 메서드
- order_history_scraping: 전체 프로세스 실행 중심부
- fetch_order_items_page_concurrent: 스레드별 병렬 API 요청
"""


import logging
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

from core.base.domain.api.base_scraping_config import BaseScrapingConfig
from core.base.storage.base_storage import BaseStorage
from core.base.storage.spec.base_save_spec import BaseStorageSaveSpec
from domain.platform.platform import Platform
from util.api_util import (
    get_expected_status_response_safely_with_retries,
    is_duplicate_snos,
    get_snos_hash,
)
from util.runtime_environment_util import get_recommended_workers_count
from util.json_util import extract_flat_values_from_json, extract_target_data
from util.logging_util import run_with_logging, logging_error_event, logging_file_event
from util.datetime_util import MILLISECONDS_PER_SECOND, parse_date_by_str, parse_time_by_str


def fetch_order_items_page_concurrent(
        scraping_config: BaseScrapingConfig,
        page: int,
        term_start: datetime,
        term_end: datetime,
        stop_flags: list,
        thread_index: int,
        seen_sno_hashes: set,
        lock: threading.Lock
):
    """
    플랫폼별 API 를 통한 주문 내역 데이터 수집 및 데이터 반환

    - 여러 플랫폼의 스크래핑 설정 처리 가능한 공통 BaseScrapingConfig 인터페이스 이용
    - API 를 통한 주문 내역 데이터 수집
    - 플랫폼별 검색 가능 최대 기한 (term) 단위 API 요청
    - 플랫폼별 다양한 API 종료 방식 방어 (중복/빈 response 반환 방어)
    - JSON 포맷 key 평탄화 (재귀적 네이밍 규칙 적용, 컬럼명으로 설정)

    :param scraping_config: 플랫폼별 스크랩 관련 설정값을 가진 인스턴스
    :param page: API 요청 페이지
    :param term_start: API 요청 시작 날짜
    :param term_end: API 요청 끝 날짜
    :param stop_flags: 스레드별 중단 여부 flag 리스트
    :param thread_index: 해당 스레드 인덱스
    :param seen_sno_hashes: API sno 중복 확인을 위한 hash 리스트
    :param lock: seen_sno_hashes 동시성 제어를 위한 lock 객체
    :return: API 수집된 데이터 Optional[list[dict]]
    """

    logging.info(f"[START] term={term_start}~{term_end}, page={page}, thread_index={thread_index}: API request")

    # 스레드별 종료 이벤트 (flag) 검증
    if stop_flags[thread_index].is_set():
        logging.debug(f"[STOP] term={term_start}~{term_end}, page={page}, thread_index={thread_index}: "
                      f"Stop flag detected")
        logging.info(f"[STOP] term={term_start}~{term_end}, page={page}, thread_index={thread_index}: "
                     f"Stop flag detected - reached end of order pages")
        return None

    # API reqeust
    response = get_expected_status_response_safely_with_retries(
        method=scraping_config.get_method(),
        base_url=scraping_config.get_base_url(),
        params=scraping_config.get_query_params(
            page=page,
            start_date=term_start.date().isoformat(),
            start_time=term_start.time().isoformat(),
            end_date=term_end.date().isoformat(),
            end_time=term_end.time().isoformat(),
        ),
        headers=scraping_config.get_headers(),
        expected_status_codes=scraping_config.get_api_expected_success_status_codes(),
        max_retries=3,
        delay_seconds=1.0,
        log_keys=["page", "term_start", "term_end"]
    )

    # 필요 데이터 추출 및 데이터 key 명 formatting
    json_data = response.json()
    order_items = extract_target_data(data=json_data, json_target_data_path=scraping_config.get_json_target_data_path())

    # request 로 빈 데이터 여부를 검증하여 API 종료 여부 검증
    if not order_items:
        logging.info(f"[STOP] term={term_start}~{term_end}, page={page}, thread_index={thread_index}: "
                     f"No order_items returned")
        stop_flags[thread_index].set()
        return None

    # request 데이터 들의 pk set 을 중복 검증하여 API 종료 여부 검증
    current_snos = [item[scraping_config.get_json_target_data_pk_name()] for item in order_items]
    with lock:
        if is_duplicate_snos(current_snos, seen_sno_hashes):
            logging.info(f"[STOP] term={term_start}~{term_end}, page={page}, thread_index={thread_index}: "
                         f"Duplicate sno detected - terminating thread")
            stop_flags[thread_index].set()
            return None

        seen_sno_hashes.add(get_snos_hash(current_snos))

    logging.info(f"[END] term={term_start}~{term_end}, page={page}, "
                 f"thread_index={thread_index}, order_history_count={len(order_items)}: "
                 f"API response")
    return order_items


@run_with_logging(
    lambda *args, **kwargs: (
        {"platform": kwargs["platform"].get_platform_eng_name()}
        if kwargs.get("platform") is not None
        else {}
    )
)
def order_history_scraping(
        platform: Optional[Platform],
        scraping_config: BaseScrapingConfig,
        storage: BaseStorage,
        save_spec: BaseStorageSaveSpec,
        max_workers: int = get_recommended_workers_count(),
) -> None:
    """
    플랫폼별 API 를 통한 주문 내역 데이터 수집 및 저장 관련 중심부

    동작 방식
    - 플랫폼별 검색 가능 최대 기한 (term) 단위 계산
    - 많은 양의 API 요청 및 데이터 처리를 위한 병렬 처리 및 동시성 제어
    - storage, save_spec 기반 저장

    :param platform: 주문 내역 수집 대상 데이터의 플랫폼 정보 Optional[Platform]
                     (로그 처리를 위한 인자이며, 반드시 keyword argument 방식으로 인자를 넘겨야 함)
    :param scraping_config: 플랫폼별 스크랩 관련 설정값을 가진 인스턴스
    :param storage: 저장소 환경별 save/load 로직을 가진 BaseStorage
    :param save_spec: 저장소 환경별 save 관련 세부 설정값을 가진 BaseStorageSaveSpec
    :param max_workers: 병렬 처리 설정 관련 최대 스레드 수
    :return: 없음
    """

    # API request 설정
    start_date = parse_date_by_str(scraping_config.get_scraping_start_date())
    end_date = parse_date_by_str(scraping_config.get_scraping_end_date())
    start_time_str = scraping_config.get_scraping_start_time()
    end_time_str = scraping_config.get_scraping_end_time()

    start_datetime = datetime.combine(
        start_date, parse_time_by_str(start_time_str) if start_time_str else datetime.min.time()
    )
    end_datetime = datetime.combine(
        end_date, parse_time_by_str(end_time_str) if end_time_str else datetime.max.time().replace(microsecond=0)
    )

    # API scrap term 추출
    safe_term_limit_ms = scraping_config.get_scraping_safe_term_limit_ms()

    if safe_term_limit_ms is None or \
            (end_datetime - start_datetime).total_seconds() * MILLISECONDS_PER_SECOND <= safe_term_limit_ms:
        term_ranges = [(start_datetime, end_datetime)]
    else:
        term_ranges = []
        term_delta = timedelta(milliseconds=safe_term_limit_ms)
        current_start = start_datetime

        while current_start < end_datetime:
            current_end = min(current_start + term_delta, end_datetime)
            term_ranges.append((current_start, current_end))
            current_start = current_end

    # 데이터 저장 dict
    rows: dict[str, dict] = {}

    # 필요 데이터 key 추출
    target_keys = list(scraping_config.get_flatten_format_json_attribute_mapping().keys())

    # 목표 데이터의 key 가 실제 API json key 에 존재하는지 검증을 위한 set
    missing_keys = set()

    # API request / 데이터 추출
    for term_start, term_end in term_ranges:
        # 동시성 및 스레드별 종료 이벤트 관련 설정
        stop_flags = [threading.Event() for _ in range(max_workers)]
        seen_page_hashes = set()
        lock = threading.Lock()

        # 병렬 API request
        def worker(thread_index):
            page = thread_index + 1
            while not stop_flags[thread_index].is_set():
                try:
                    items = fetch_order_items_page_concurrent(
                        scraping_config=scraping_config,
                        page=page,
                        term_start=term_start,
                        term_end=term_end,
                        stop_flags=stop_flags,
                        thread_index=thread_index,
                        seen_sno_hashes=seen_page_hashes,
                        lock=lock,
                    )

                    if items is None:
                        break

                    # request 데이터 들의 pk set 을 중복 검증하여 API 의 종료 여부 검증
                    for item in items:
                        json_sno = item[scraping_config.get_json_target_data_pk_name()]
                        if json_sno is None:
                            logging.warning(f"[SKIP] json_sno={json_sno}: Invalid sno value")
                            continue

                        sno = str(json_sno)
                        with lock:
                            if rows.get(sno) is not None:
                                continue

                            # 검증된 request 데이터 평탄화 및 삽입
                            flat_data = extract_flat_values_from_json(item)

                            row = {}
                            for key in target_keys:
                                if key not in flat_data:
                                    missing_keys.add(key)

                                row[key] = flat_data.get(key)

                            rows[sno] = row

                    page += max_workers

                except Exception as e:
                    logging_error_event(
                        exception_instance=e,
                        log_metadata={"thread_index": thread_index},
                        log_message=f"While request API with concurrency",
                        log_message_detail=str(e),
                    )
                    break

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for idx in range(max_workers):
                executor.submit(worker, idx)

    # 목표 데이터의 key 중 실제 API json key 에 존재하지 않는 key 로그 처리
    # 단, 구조상 누락이 자연스러운 key 도 존재할 수 있으니 참고용으로 활용
    if missing_keys:
        # list 데이터의 경우 '{같은 컬럼명}.{index}' 의 key 가 여럿 존재하므로 로그를 위해 간소화
        simplified_missing_keys = set(
            re.sub(r"\.\d+(\.|$)", ".{index}\\1", key)
            for key in missing_keys
        )

        logging.warning(f"[FORMAT] missing_keys={list(simplified_missing_keys)}: "
                        f"Found missing keys in API response data - "
                        f"check target keys or API format changed")

    # rows 개별 key 명 변경
    renamed_rows = {
        pk: {
            scraping_config.get_flatten_format_json_attribute_mapping().get(k, k): v
            for k, v in row.items()
        }
        for pk, row in rows.items()
    }

    # 저장
    storage.save(
        save_spec=save_spec,
        df=pd.DataFrame(renamed_rows.values()),
    )
    logging_file_event(file_path=save_spec.get_full_path(), log_prefix="SAVE")
