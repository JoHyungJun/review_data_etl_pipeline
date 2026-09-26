"""
dynamic_bucket_util.py
----------------------

감성 추론 모델 및 과정의 dynamic bucketing 관련 util 모듈
"""


from dataclasses import dataclass


@dataclass(slots=True)
class DynamicBucketEntry:
    """
    Dynamic bucketing 과정에서 사용되는 개별 text 단위 데이터 객체

    주요 역할
    - 원본 text 데이터와 original index (순서) 및 개별 text 의 token count 정보 관리
    - dynamic bucketing 과정의 기준 데이터 역할
    """

    original_idx: int
    text: str
    token_count: int


def build_dynamic_buckets(
        bucket_entries: list[DynamicBucketEntry],
        optimal_token_count_per_batch: int,
        min_padding_efficiency_ratio: float,
) -> list[list[DynamicBucketEntry]]:
    """
    파라미터로 들어온 DynamicBucketEntry 데이터들 (list) 에 dynamic bucketing 로직을 적용하여
    전체 데이터를 batch (list[DynamicBucketEntry]) 단위의 list 로 반환

    동작 방식
    - token count 기준 sort
    - 비슷한 token count 의 데이터끼리 bucket 구성
      (개별 bucket 내부 데이터들은 token count 차이가 min_padding_efficiency_ratio 를 넘지 않도록 설계)
    - 개별 bucket 에 담긴 데이터들의 총 token count 가 optimal_token_count_per_batch 를 넘지 않도록 설계
      (총 token count 는 padding 을 포함한 크기)

    주의 사항
    - dynamic bucketing 과정 중 sort 로 인해 기존 데이터의 순서가 바뀔 수 있으므로,
      순서를 보장해야 하는 호출부 로직에선 DynamicBucketEntry.original_idx 기준의 재정렬을 권고
    - OOM 에러를 방어하는 fallback 로직에서도 해당 메서드 재활용 가능

    :param bucket_entries: dynamic bucketing 대상 list[DynamicBucketEntry]
    :param optimal_token_count_per_batch: 개별 bucket (batch) 이 담을 수 있는 최대 토큰 개수 int
    :param min_padding_efficiency_ratio: 개별 bucket (batch) 내부 개별 원소끼리의 허용 가능 토큰 개수 비율 float
    :return: dynamic bucketing 로직이 적용된 buckets list[list[DynamicBucketEntry]]
    """

    sorted_bucket_entries = sorted(bucket_entries, key=lambda x: x.token_count)

    batches: list[list[DynamicBucketEntry]] = [[]]
    for sorted_bucket_entry in sorted_bucket_entries:
        current_token_count = sorted_bucket_entry.token_count

        last_bucket = batches[-1]

        if not last_bucket:
            last_bucket.append(sorted_bucket_entry)
            continue

        # sort 가 선행되었지만 구조 변경 가능성을 고려하여, 명확히 매 loop 마다 min/max 계산
        last_bucket_token_counts = [x.token_count for x in last_bucket]

        last_bucket_min_token_count = min(last_bucket_token_counts)
        last_bucket_max_token_count = max(last_bucket_token_counts)

        # 현재 원소가 포함 되었을 때 예측되는 padding 을 포함한 총 토큰 수 계산
        potential_max_token = max(current_token_count, last_bucket_max_token_count)
        potential_min_token = min(current_token_count, last_bucket_min_token_count)

        if potential_max_token * (len(last_bucket) + 1) <= optimal_token_count_per_batch:

            # padding 비율 비교
            if potential_min_token / potential_max_token >= min_padding_efficiency_ratio:
                last_bucket.append(sorted_bucket_entry)
                continue

        batches.append([sorted_bucket_entry])

    return batches
