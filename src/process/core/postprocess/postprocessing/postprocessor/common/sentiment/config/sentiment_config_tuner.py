"""
sentiment_config_tuner.py
-------------------------

감성 추론 관련 로그를 분석하고
계산 값을 외부 감성 추론 관련 설정 파일 및 SentimentConfig 에 수정 및 반영하는 클래스 모듈
"""


import json
import logging
import threading
from dataclasses import asdict
from typing import cast

import numpy as np

from process.core.postprocess.postprocessing.postprocessor.common.sentiment.config.sentiment_config import \
    SentimentConfig
from process.core.postprocess.postprocessing.postprocessor.common.sentiment.config.util.tuning_util import \
    calculate_optimal_max_text_length, calculate_optimal_memory_usage_ratio
from process.core.postprocess.postprocessing.postprocessor.common.sentiment.log.model.logger.sentiment_config_tuner_statistics_meta_logger import \
    SentimentConfigTunerStatisticsMetaLogger
from process.core.postprocess.postprocessing.postprocessor.common.sentiment.log.model.logger.sentiment_event_logger import \
    SentimentEventLogger

from process.core.postprocess.postprocessing.postprocessor.common.sentiment.log.model.models import (
    SentimentConfigTunerStatisticsMetaLog,
    SentimentInferredLog,
    SentimentIntervalStatisticsLog,
    SentimentConfigTunerMetaLog,
    SentimentOOMFallbackLog,
    BaseSentimentLog,
)
from process.core.postprocess.postprocessing.postprocessor.common.sentiment.log.util.log_util import \
    group_sentiment_logs_by_event_type
from process.core.postprocess.postprocessing.postprocessor.common.sentiment.model.sentiment_model import SentimentModel
from process.core.postprocess.postprocessing.postprocessor.common.sentiment.type.event_types import \
    SentimentLogEventType
from util.datetime_util import get_current_datetime
from util.jsonl_util import load_lines_before_byte_from_jsonl
from util.logging_util import logging_error_event
from util.path_util import get_or_create_directory


class SentimentConfigTuner:
    """
    감성 추론 모델 동적 설정 정보 조정 클래스
    
    감성 추론 관련 로그를 분석하고
    계산 값을 외부 감성 추론 관련 설정 파일 및 SentimentConfig 에 수정 및 반영하는 클래스

    해당 객체는 static 한 성격으로 별도의 객체 생성 없이 class method 로 활용할 수 있으며,
    tuning 에 활용되는 로그 파일들의 IO 작업에 대한 방어 코드가 작성되어 있지만
    애플리케이션 실행 전, tuner 가 활용하는 로그 파일에 대한 초기화의 선행을 권고
    """

    # config constants
    DEFAULT_MIN_RATIO = 0.4
    DEFAULT_MAX_RATIO = 0.8
    DEFAULT_RATIO_STEP = 0.05

    # 12 개월, 혹은 계절 (12주) 기준
    INTERVAL_CHUNK_SIZE = 12

    # config class
    event_logger = SentimentEventLogger
    tuner_logger = SentimentConfigTunerStatisticsMetaLogger

    inferred_log_model = SentimentInferredLog
    tuner_log_model = SentimentConfigTunerStatisticsMetaLog

    sentiment_config = SentimentConfig

    # lock
    _tuning_lock = threading.Lock()

    @classmethod
    def run(cls):
        """
        통계, 메타 로그를 기반으로 tuning 을 관장하는 orchestration 호출부

        로그 데이터 load, fallback 분기 처리는 해당 메서드에서 모두 수행

        동작 방식
        - 다양한 파일에 대한 IO 작업에 의해 동시성 처리 (lock)
        - 감성 추론 관련 수집된 로그 및 통계, 메타 로그 간의 정합성 검증 및 fallback 수행
        - tuning 대상 구간의 감성 추론 결과 로그를 분석하여 최적화된 새로운 값을 가진 SentimentConfig 생성
        - 애플리케이션 실행 중 싱글톤으로 관리되는 전역 SentimentModel, SentimentLogger 에 접근하여,
          내부적으로 관리하고 있는 SentimentConfig 를 교체 및 설정 파일을 다시 write

        :return: 없음
        """

        with cls._tuning_lock:

            # 필요한 변수 추출
            tuner_log_file_path = cls.tuner_logger.get_storage_path()
            event_log_file_path = cls.event_logger.get_storage_path()

            event_log_file_size = event_log_file_path.stat().st_size

            # ==================== #
            # logs load & fallback #
            # ==================== #

            tuner_logs, _ = cls.tuner_logger.full_scan_logs()
            tuner_logs = cast(list[cls.tuner_log_model], tuner_logs)

            # statistical meta data load
            latest_tuner_log = (
                tuner_logs[-1]
                if tuner_logs
                else None
            )

            # validate
            is_required_full_scan = False
            latest_meta_log = None

            # 메타 로그가 없다면 event 로그 full scan 대상
            if latest_tuner_log is None:
                logging.warning(
                    f"[FAILED] process=tuning_config, "
                    f"path={tuner_log_file_path}: "
                    f"Not found meta log file "
                    f"- attempting to fallback logic (make path or file with full scan, remove previous file)"
                )
                is_required_full_scan = True

            # 메타 로그가 있다면 정합성 확인
            else:
                latest_meta_log = latest_tuner_log.sentiment_config_tuner_meta_log

                # 정합성 검사
                # statistical meta data log 의 정합성 검사
                if latest_meta_log.last_read_cursor_byte > latest_meta_log.last_read_file_byte_size:
                    logging.warning(
                        f"[WARN] process=tuning_config, "
                        f"last_read_byte_offset={latest_meta_log.last_read_cursor_byte}, "
                        f"last_read_file_byte_size={latest_meta_log.last_read_file_byte_size}: "
                        f"Detected inconsistency in sentiment config tuner statistics meta log "
                        f"- attempting to fallback logic (make new statistics meta log with full scan)"
                    )
                    is_required_full_scan = True

                # statistical meta data log 와 event log 의 파일 크기 기록 정합성 검사
                if latest_meta_log.last_read_file_byte_size > event_log_file_size:
                    logging.warning(
                        f"[WARN] process=tuning_config, "
                        f"last_read_byte_offset={latest_meta_log.last_read_cursor_byte}, "
                        f"event_log_file_size={event_log_file_size}: "
                        f"Detected inconsistency between meta log and event log "
                        f"- attempting to fallback logic (make new statistics meta log with full scan)"
                    )
                    is_required_full_scan = True

            # 정합성 검사를 모두 통과했다면 기존 메타 로그 유지, 마지막 tuning ~ 현재 시점까지의 데이터만 interval scan
            if not is_required_full_scan:
                # event log load
                tuner_last_read_event_dicts = load_lines_before_byte_from_jsonl(
                    file_path=event_log_file_path,
                    end_byte=latest_meta_log.last_read_cursor_byte,
                )

                # event logs 파일이 invalid 한 상태이거나 파싱 중 에러의 경우, meta 와 정합성이 깨진 상태
                tuner_last_read_event_log = None
                try:
                    tuner_last_read_event_log = (
                        BaseSentimentLog.from_dict(tuner_last_read_event_dicts[0])
                        if tuner_last_read_event_dicts
                        else None
                    )
                except Exception as e:
                    logging.warning(
                        f"[WARN] process=tuning_config, "
                        f"path={event_log_file_path}, "
                        f"Detected invalid state while loading sentiment event log file "
                        f"- {str(e)}"
                    )
                    is_required_full_scan = True

                # statistical meta data log 와 event log 의 timestamp 기록 정합성 검사
                if (
                        tuner_last_read_event_log is not None
                        and latest_meta_log.last_tuned_log_timestamp != tuner_last_read_event_log.timestamp
                ):
                    logging.warning(
                        f"[WARN] process=tuning_config, "
                        f"last_tuned_log_timestamp={latest_meta_log.last_tuned_log_timestamp}, "
                        f"tuner_last_read_event_log_timestamp={tuner_last_read_event_log.timestamp}: "
                        f"Detected inconsistency between meta log and event log "
                        f"- attempting to fallback logic (make new statistics meta log with full scan)"
                    )
                    is_required_full_scan = True

            # 정합성 검사 중 하나라도 통과되지 않았다면 기존 메타 로그를 모두 지우고, full scan
            if is_required_full_scan:
                cls.tuner_logger.clear_logs()

                tuner_logs = []
                latest_meta_log = None

            current_interval_event_logs, latest_end_of_line_byte = cls.event_logger.read_logs_between_bytes(
                start_byte=latest_meta_log.last_read_cursor_byte if latest_meta_log else None,
                end_byte=event_log_file_size,
            )

            # 해당 구간 내에 tuning 할 로그가 존재하지 않는다면 return
            if not current_interval_event_logs:
                return

            # ================================ #
            # create/write meta/statistics log #
            # ================================ #

            current_datetime = get_current_datetime()

            logs_grouped_by_event_type = group_sentiment_logs_by_event_type(current_interval_event_logs)
            inferred_logs = (
                    logs_grouped_by_event_type.get(SentimentLogEventType.INFERRED)
                    or []
            )

            try:
                current_tuner_log = cls.tuner_log_model(
                    timestamp=current_datetime,

                    sentiment_interval_statistics_log=cls._create_interval_statistics_log(
                        inferred_logs=inferred_logs,
                    ),

                    sentiment_config_tuner_meta_log=SentimentConfigTunerMetaLog(
                        timestamp=current_datetime,

                        tuned_log_count=len(current_interval_event_logs),

                        last_read_file_byte_size=event_log_file_size,
                        last_read_cursor_byte=latest_end_of_line_byte,
                        last_tuned_log_timestamp=current_interval_event_logs[-1].timestamp,
                    )
                )
            except Exception as e:
                raise ValueError(
                    f"튜닝을 위한 로그 수집 중 정합성에 맞지 않는 로그 데이터가 검출되었습니다. "
                    f"로그 파일을 확인해주세요. : {str(e)}"
                )

            cls.tuner_logger.write_log(current_tuner_log)

            # ================= #
            # tune/write config #
            # ================= #

            sentiment_config_from_current_file = cls.sentiment_config.load()

            oom_logs = (
                    logs_grouped_by_event_type.get(SentimentLogEventType.OOM_FALLBACK)
                    or []
            )
            statistics_logs = [
                *(tuner_log.sentiment_interval_statistics_log for tuner_log in tuner_logs),
                current_tuner_log.sentiment_interval_statistics_log,
            ]

            tuned_config = cls._create_tuned_config(
                previous_config=sentiment_config_from_current_file,
                statistics_logs=statistics_logs,
                inferred_logs=inferred_logs,
                oom_logs=oom_logs,
            )

            cls._write_config(tuned_config)


    @classmethod
    def _write_config(cls, sentiment_config: SentimentConfig) -> None:
        """
        감성 추론 config 객체 정보를 config 파일에 write

        주의 사항
        - config 파일에 대한 write 책임은 해당 tuner 클래스가 가지고 있으며,
          따라서 tuner 가 아닌 다른 곳에서의 config 파일 작성 금지를 권고

        :param sentiment_config: 작성 대상 값을 가진 설정 객체 SentimentConfig
        :return: 없음
        """

        config_file_path = get_or_create_directory(full_path=cls.sentiment_config.CONFIG_FILE_PATH)

        try:
            with open(config_file_path, "w", encoding="utf-8") as file:
                json.dump(asdict(sentiment_config), file, indent=4)
        except Exception as e:
            logging_error_event(
                exception_instance=e,
                log_message="While writing sentiment config file",
                log_metadata={
                    "file_path": config_file_path,
                },
            )
            raise


    @classmethod
    def _create_tuned_config(
            cls,
            previous_config: SentimentConfig,
            statistics_logs: list[SentimentIntervalStatisticsLog],
            inferred_logs: list[SentimentInferredLog],
            oom_logs: list[SentimentOOMFallbackLog],
    ) -> SentimentConfig:
        """
        이전 감성 추론 관련 config 설정값 및 수집된 감성 추론 관련 로그들을 기반하고 분석하여
        tuning 된 새로운 감성 추론 관련 설정값을 가진 sentiment config 객체 반환

        TODO:
            이후 추가적인 정보 수집 혹은 수정 대상 설정값이 늘어난다면 해당 메서드에 반영 예정

        :param previous_config: 이전 감성 추론 관련 설정 객체 SentimentConfig
        :param statistics_logs: 분석 대상 통계 관련 로그 list[SentimentIntervalStatisticsLog]
        :param inferred_logs: 분석 대상 감성 추론 성공 로그 list[SentimentInferredLog]
        :param oom_logs: 분석 대상 감성 추론 OOM 실패 로그 list[SentimentOOMFallbackLog]
        :return: tuning 된 새로운 감성 추론 관련 설정값을 가진 설정 객체 SentimentConfig
        """

        return SentimentConfig(
            max_text_length=calculate_optimal_max_text_length(
                interval_statistics_logs=statistics_logs,
                statistics_chunk_size=cls.INTERVAL_CHUNK_SIZE,
            ),
            memory_usage_ratio=calculate_optimal_memory_usage_ratio(
                inferred_logs=inferred_logs,
                oom_logs=oom_logs,
                previous_memory_usage_ratio=previous_config.memory_usage_ratio,
                min_memory_ratio=cls.DEFAULT_MIN_RATIO,
                max_memory_ratio=cls.DEFAULT_MAX_RATIO,
                growth_ratio_step=cls.DEFAULT_RATIO_STEP,
            ),
            oom_token_reduction_ratio=previous_config.oom_token_reduction_ratio,
            min_padding_efficiency_ratio=previous_config.min_padding_efficiency_ratio,
            min_throughput_improvement_ratio=previous_config.min_throughput_improvement_ratio,
            measure_count=previous_config.measure_count,
        )


    @classmethod
    def _create_interval_statistics_log(
            cls,
            inferred_logs: list[SentimentInferredLog],
    ) -> SentimentIntervalStatisticsLog:
        """
        구간별 수집된 inferred logs 를 기반하여 통계 정보를 담은 로그 객체 생성

        :param inferred_logs: 구간별 수집된 통계 정보 로그 변환 대상 list[SentimentInferredLog]
        :return: 수집 정보 기반 SentimentIntervalStatisticsLog
        """

        # 데이터 분석 및 통계 누적
        model = SentimentModel
        config = model.get_config()

        current_applied_optimal_token_count_per_batch = model.get_optimal_token_count_per_batch()
        current_applied_max_text_length = config.max_text_length

        # 추론한 텍스트 개수
        current_text_count = 0
        current_positive_text_count = 0
        current_negative_text_count = 0
        
        total_text_token_length_mappings = []

        for inferred_log in inferred_logs:
            batch_snapshot = inferred_log.batch_snapshot
            batch_snapshot_summary = batch_snapshot.batch_snapshot_summary

            # 논리적 정합성 검증
            if batch_snapshot_summary.batch_size != len(batch_snapshot.text_token_length_mappings):
                raise ValueError(
                    f"통계 로그 분석 중 배치 내부 추론 대상 문장 개수 ({batch_snapshot_summary.batch_size}) 와 "
                    f"히스토그램 데이터 ({batch_snapshot.text_token_length_mappings}) 가 일치하지 않는 로그를 발견했습니다. "
                    f"로그 파일 혹은 코드를 확인해주세요."
                )

            current_text_count += batch_snapshot_summary.batch_size
            current_positive_text_count += inferred_log.positive_text_count
            current_negative_text_count += inferred_log.negative_text_count

            total_text_token_length_mappings.extend(batch_snapshot.text_token_length_mappings)

        current_text_lengths = [mapping.text_length for mapping in total_text_token_length_mappings]
        current_token_lengths = [mapping.token_length for mapping in total_text_token_length_mappings]
        
        # 추론 텍스트/토큰의 전체 길이 합
        current_total_text_length = sum(current_text_lengths)
        current_total_token_length = sum(current_token_lengths)

        current_token_to_text_ratio = (
            0
            if current_total_text_length <= 0
            else current_total_token_length / current_total_text_length
        )

        # 현재 구간의 snapshot 로그 정보 save
        return SentimentIntervalStatisticsLog(
            timestamp=get_current_datetime(),

            inferred_total_text_count=current_text_count,

            positive_text_count=current_positive_text_count,
            negative_text_count=current_negative_text_count,

            avg_text_length=(current_total_text_length / current_text_count if current_text_count > 0 else 0),
            p95_text_length=int(np.percentile(current_text_lengths, 95) if current_text_lengths else 0),

            avg_token_length=(current_total_token_length / current_text_count if current_text_count > 0 else 0),
            p95_token_length=int(np.percentile(current_token_lengths, 95) if current_token_lengths else 0),

            token_to_text_ratio=current_token_to_text_ratio,

            applied_max_text_length=current_applied_max_text_length,
            applied_optimal_token_count_per_batch=current_applied_optimal_token_count_per_batch,
        )
