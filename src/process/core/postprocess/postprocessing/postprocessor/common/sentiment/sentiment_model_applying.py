"""
sentiment_model_applying.py
---------------------------

학습된 이진 분류 감성 추론 모델로 부정적 리뷰 내용을 추출하고 필터링하는 모듈
(감성 추론 모델은 약 5000 개의 라벨링 데이터로 학습됨)

post processing 중 한 단계의 모듈 (Optional)

선행 데이터
- 학습된 감성 추론 모델 (Required): 선행 라벨링 데이터 및 colab 을 통해 학습된 감성 추론 모델
"""


import logging
import time
from collections import deque, Counter
from typing import Union, Optional

import pandas as pd
import torch

from domain.platform.platform import Platform
from process.core.postprocess.postprocessing.postprocessor.common.sentiment.constant.sentiment_label import (
    SENTIMENT_POSITIVE_LABEL,
    SENTIMENT_NEGATIVE_LABEL,
)
from process.core.postprocess.postprocessing.postprocessor.common.sentiment.log.model.models import (
    SentimentInferredLog,
    SentimentOOMFallbackLog,
    SentimentInferredFailedLog,
)
from process.core.postprocess.postprocessing.postprocessor.common.sentiment.log.model.logger.sentiment_inferred_logger import SentimentEventLogger
from process.core.postprocess.postprocessing.postprocessor.common.sentiment.model.batch_snapshot import BatchSnapshot, \
    TextTokenLengthMapping, BatchSnapshotSummary
from process.core.postprocess.postprocessing.postprocessor.common.sentiment.model.sentiment_model import SentimentModel
from process.core.postprocess.postprocessing.postprocessor.common.sentiment.util.dynamic_bucket_util import (
    DynamicBucketEntry,
    build_dynamic_buckets,
)
from process.core.postprocess.postprocessing.postprocessor.common.sentiment.util.token_batch_util import \
    calculate_token_count_by_text_length
from util.column_util import (
    validate_required_columns_in_df,
    drop_invalid_columns_data_safely,
    drop_safely,
    reindex_safely,
)
from util.datetime_util import get_current_datetime
from util.logging_util import run_with_logging
from util.runtime_environment_util import (
    is_inference_oom_exception,
    synchronize_inference_device,
    clear_inference_device_cache,
    get_device_memory_snapshot,
)


# TRAINED_SENTIMENT_MODEL_DIRECTORY_PATH
@run_with_logging(
    lambda *args, **kwargs: (
        {"platform": kwargs["platform"].get_platform_eng_name()}
        if kwargs.get("platform") is not None
        else {}
    )
)
def sentiment_model_applying(
        platform: Optional[Platform],
        df: pd.DataFrame,
        target_texts_column: str,
) -> pd.DataFrame:
    """
    문자열 데이터 정보를 기반으로 감성 추론 긍정/부정 판별 및 부정적 데이터 제외 후 반환

    주의 사항
    - 로직에 사용되는 필수 컬럼이 공백 혹은 None/NaN/Null 등 invalid 한 데이터일 경우, 해당 레코드는 제거됨
    - OOM 등의 에러 시 fallback 로직은 같은 dynamic bucketing 메서드로 재활용하되, padding 비율을 0으로 설정하여 수행
      이때, fallback 은 에러가 난 bucket 기준으로만 동작하며, 이후 bucket 은 기존 설정값으로 진행
    - 해당 로직 수행 중 발생하는 에러에 대한 상세 정보는 sentiment 전용 로그에 작성

    :param platform: 감성 추론 대상 데이터의 플랫폼 정보 Optional[Platform]
                     (로그 처리를 위한 인자이며, 반드시 keyword argument 방식으로 인자를 넘겨야 함)
    :param df: 보정 대상 pandas.DataFrame
    :param target_texts_column: 보정 대상 df 의 관련 컬럼명 str
    :return: 보정된 pandas.DataFrame
    """

    input_df_len = len(df)
    ordered_column_names = list(df.columns)

    df = df.copy()

    # 필수 컬럼 검증
    required_columns = [target_texts_column]

    validate_required_columns_in_df(
        df=df,
        column_names=required_columns,
    )

    drop_invalid_columns_data_safely(
        df=df,
        column_names=required_columns,
    )

    # dynamic bucketing 을 위해 임시 index 컬럼 생성 (개별 레코드에 index 부여)
    TEMP_INDEX_COLUMN = "_temp_index_column"

    df.reset_index(drop=True, inplace=True)
    df[TEMP_INDEX_COLUMN] = df.index

    # 감성 추론 모델에서 transformers 기반 model, tokenizer 추출
    sentiment_model = SentimentModel

    model, tokenizer = sentiment_model.get_model_and_tokenizer()
    sentiment_config = sentiment_model.get_config()

    current_bucket_max_token_count = calculate_token_count_by_text_length(
        tokenizer=tokenizer,
        text_length=sentiment_config.max_text_length,
    )

    target_texts = df[target_texts_column].astype(str).tolist()
    encoded_inputs = tokenizer(
        target_texts,
        padding=False,
        truncation=True,
        max_length=current_bucket_max_token_count,
        add_special_tokens=True,
        return_attention_mask=False,
        return_token_type_ids=False,
    )
    token_counts = [len(ids) for ids in encoded_inputs["input_ids"]]

    # 개별 리뷰의 순서 (index) 와 토큰 수 매핑
    entries = [
        DynamicBucketEntry(
            original_idx=idx,
            text=text,
            token_count=token_count,
        )
        for idx, text, token_count in zip(
            df[TEMP_INDEX_COLUMN],
            target_texts,
            token_counts,
        )
    ]

    # dynamic bucketing
    # 사용될 변수 추출
    device = sentiment_model.get_device()
    optimal_token_count_per_batch = sentiment_model.get_optimal_token_count_per_batch()

    min_padding_efficiency_ratio = sentiment_config.min_padding_efficiency_ratio
    oom_token_reduction_ratio = sentiment_config.oom_token_reduction_ratio

    batches = build_dynamic_buckets(
        bucket_entries=entries,
        optimal_token_count_per_batch=optimal_token_count_per_batch,
        min_padding_efficiency_ratio=min_padding_efficiency_ratio,
    )

    entry_index_inferred_label_mapping: dict[int, int] = {}
    bucket_queue = deque(batches)

    while bucket_queue:
        # 토크나이징 및 모델 적용 로직
        current_bucket = bucket_queue.popleft()

        if not current_bucket:
            continue

        inputs = None
        outputs = None

        try:
            current_bucket_texts = [
                entry.text
                for entry in current_bucket
            ]

            # latency 측정 (start)
            batch_started_at = time.perf_counter()

            inputs = tokenizer(
                current_bucket_texts,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=current_bucket_max_token_count,
                add_special_tokens=True,
                return_token_type_ids=False,
            )

            inputs = {
                k: v.to(device)
                for k, v in inputs.items()
            }

            with torch.inference_mode():
                outputs = model(**inputs)

            # latency 측정 (end)
            synchronize_inference_device(device)
            elapsed_ms = (time.perf_counter() - batch_started_at) * 1000

            current_bucket_labels = (
                outputs
                .logits             # 개별 긍/부정 점수 행렬
                .argmax(dim=1)      # 각 text 마다 긍/부정 중 높은 점수 쪽의 index 추출
                .tolist()           # list 형태로 변환
            )

            # sentiment 전용 로그 처리
            label_counts = Counter(current_bucket_labels)

            SentimentEventLogger.write_log(
                SentimentInferredLog(
                    timestamp=get_current_datetime(),

                    batch_snapshot=BatchSnapshot.from_text_token_length_mappings(
                        text_token_length_mappings=[
                            TextTokenLengthMapping(
                                text_length=len(entry.text),
                                token_length=entry.token_count,
                            )
                            for entry in current_bucket
                        ]
                    ),

                    positive_text_count=label_counts[SENTIMENT_POSITIVE_LABEL],
                    negative_text_count=label_counts[SENTIMENT_NEGATIVE_LABEL],

                    device=device,

                    elapsed_ms=elapsed_ms,
                )
            )

            # 결과 labeling
            for entry, label in zip(current_bucket, current_bucket_labels):
                entry_index_inferred_label_mapping[entry.original_idx] = label

        # 추론 실패
        except Exception as e:

            # 로그용 공통 정보 추출
            original_batch_snapshot_summary = BatchSnapshotSummary.from_text_token_length_mappings(
                text_token_length_mappings=[
                    TextTokenLengthMapping(
                        text_length=len(entry.text),
                        token_length=entry.token_count,
                    )
                    for entry in current_bucket
                ]
            )

            # 실패 시 원인 찾기 및 로그 처리를 위해 현 시점의 메모리 상태 추출
            current_memory_snapshot = get_device_memory_snapshot(device)
            
            # 메모리 관련 에러일 경우 조건에 따라 fallback 적용
            # 단일 텍스트가 들어간 bucket 마저 처리하지 못할 경우 에러로 간주
            if is_inference_oom_exception(e, device) and len(current_bucket) > 1:
                # 전역/sentiment 전용 로그 처리
                logging.warning(
                    f"[FAILED] device={device}, bucket_length={len(current_bucket)}, error={e}: "
                    f"Detected Out-Of-Memory error while applying sentiment model"
                )

                # 공간 확보
                # 현재 bucket 의 tensor 를 들고 있는 변수 할당 제거
                if inputs is not None:
                    del inputs
                if outputs is not None:
                    del outputs

                # 추론 모델 관련 캐시 제거
                clear_inference_device_cache(device)

                # fallback 을 위해 현재 bucket 을 나누어 다시 dynamic bucketing
                current_bucket_total_token_count = original_batch_snapshot_summary.total_token_count_per_batch
                reduced_max_tokens_per_batch = max(
                    int(current_bucket_total_token_count * oom_token_reduction_ratio), 1
                )

                # 이미 해당 bucket 의 padding 은 최초 dynamic bucketing 에서 맞춰졌으므로, 0으로 설정
                fallback_buckets = build_dynamic_buckets(
                    bucket_entries=current_bucket,
                    optimal_token_count_per_batch=reduced_max_tokens_per_batch,
                    min_padding_efficiency_ratio=0,
                )

                # append left 특성에 의해 reversed 후 삽입
                for fallback_bucket in reversed(fallback_buckets):
                    bucket_queue.appendleft(fallback_bucket)

                # 새로운 bucket 에 대해 로그 처리
                ordered_fallback_batch_snapshot_summaries = [
                    BatchSnapshotSummary.from_text_token_length_mappings(
                        text_token_length_mappings=[
                            TextTokenLengthMapping(
                                text_length=len(entry.text),
                                token_length=entry.token_count,
                            )
                            for entry in fallback_bucket
                        ]
                    )
                    for fallback_bucket in fallback_buckets
                ]

                SentimentEventLogger.write_log(
                    SentimentOOMFallbackLog(
                        timestamp=get_current_datetime(),

                        original_batch_snapshot_summary=original_batch_snapshot_summary,
                        fallback_batch_snapshot_summaries=ordered_fallback_batch_snapshot_summaries,

                        device=device,

                        error_message=str(e),

                        memory_snapshot=current_memory_snapshot,
                    )
                )


            # 다른 종류의 에러일 경우 설정 및 환경 자체의 문제일 경우를 고려하여 에러 발생
            else:

                logging.exception(
                    f"[ERROR] device={device}, bucket_length={len(current_bucket)}, error={e}: "
                    f"Detected unexpected error while applying sentiment model"
                )

                # 추론 실패 시 sentiment 전용 로그 처리
                SentimentEventLogger.write_log(
                    SentimentInferredFailedLog(
                        timestamp=get_current_datetime(),

                        batch_snapshot_summary=BatchSnapshotSummary.from_text_token_length_mappings(
                            text_token_length_mappings=[
                                TextTokenLengthMapping(
                                    text_length=len(entry.text),
                                    token_length=entry.token_count,
                                )
                                for entry in current_bucket
                            ]
                        ),

                        device=device,

                        exception_type=type(e).__name__,
                        error_message=str(e),

                        memory_snapshot=current_memory_snapshot,
                    )
                )

                raise

    # 추론 결과와 기존 df 를 index 기준으로 매핑 및 검증
    TEMP_INFERRED_LABEL_COLUMN = "_temp_inferred_label_column"
    df[TEMP_INFERRED_LABEL_COLUMN] = (
        df[TEMP_INDEX_COLUMN]
        .map(entry_index_inferred_label_mapping)
    )

    if df[TEMP_INFERRED_LABEL_COLUMN].isna().any():
        raise RuntimeError(
            f"감성 추론 이후 결과물을 매핑하는 과정에서 알 수 없는 이유로 빈 데이터가 검출되었습니다. "
            f"로그 및 코드를 확인해주세요."
        )

    # 부정 리뷰 제거
    df = df[
        df[TEMP_INFERRED_LABEL_COLUMN] == SENTIMENT_POSITIVE_LABEL
    ].copy()

    # 최종 포맷팅 (임시 컬럼 제거 / index 순서 조절)
    drop_safely(
        df=df,
        column_names=[
            TEMP_INDEX_COLUMN,
            TEMP_INFERRED_LABEL_COLUMN,
        ]
    )

    df.reset_index(drop=True, inplace=True)

    logging.info(f"[END] input_df_len={input_df_len}, processed_df_len={len(df)}")

    df = reindex_safely(
        df=df,
        column_names=ordered_column_names,
        is_strict=True,
    )
    return df
