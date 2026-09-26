"""
tuning_util.py
--------------

감성 추론 로그들의 분석 및 설정값 계산 관련 util 모듈
"""
from typing import Union

import numpy as np

from process.core.postprocess.postprocessing.postprocessor.common.sentiment.log.model.models import \
    SentimentIntervalStatisticsLog, SentimentInferredLog, SentimentOOMFallbackLog


def calculate_optimal_max_text_length(
        interval_statistics_logs: list[SentimentIntervalStatisticsLog],
        statistics_chunk_size: int,
        min_statistics_chunk_count: int = 2,
) -> int:
    """
    가중 선형 회귀 로직을 적용하여 max text length (P95) 값 추론

    해당 로직은 감성 추론을 통과한 text 들에 대해
    text length 의 P95 값을 전체 계산이 아닌 간접 도출하기 위해 활용되며,

    text length 의 시간별 추이를 확인하기 위해,
    최근 text length chunk 일수록 높은 가중치를 부여하는 가중 선형 회귀 로직을 채택

    주의 사항
    - 해당 메서드로 추론된 결과는 정밀한 데이터 분석 방식을 적용한 것이 아닌 단순 추론 값임을 염두
    - 해당 메서드의 최소 log 개수는
      개별 chunk 에 들어갈 통계 로그 개수 (statistics_chunk_size) * 분석을 위한 최소 chunk 개수 (min_statistics_chunk_count)
    - 선형 회귀 계산을 위해 min_statistics_chunk_count 값은 최소한 2 이상의 값을 가져야 함

    동작 방식
    - 유의미한 추론을 할 수 있는 최소 로그 개수 검증
    - 구간별로 수집된 통계 로그를 chunk 단위 개수로 나누고,
      개별 chunk 마다의 평균값 계산
    - chunk 별로 수집 기한에 따라 차등 가중치를 부여하여
      가중 선형 회귀 방정식 추출
    - 마지막 chunk 가 아직 완전히 수집되지 않은 경우,
      chunk 진행률 (last_chunk_size / statistics_chunk_size) 을 기반하여 선형 회귀 방정식의 x 값으로 설정
    - 현재 시점에서의 추정 max text length (P95) 반환


    :param interval_statistics_logs: 감성 추론 통계 로그 list[SentimentIntervalStatisticsLog]
    :param statistics_chunk_size: 개별 chunk 에 들어갈 통계 로그 개수 int
    :param min_statistics_chunk_count: 분석을 위한 최소 chunk 개수 int
    :return: 가중 선형 회귀를 chunk 단위로 적용하여 추론된 max text length (P95) int
    """

    if (
            not interval_statistics_logs
            or len(interval_statistics_logs) < statistics_chunk_size * min_statistics_chunk_count
    ):
        raise ValueError("분석 대상 통계 로그의 개수가 부족합니다. 코드 혹은 파일을 확인해주세요.")

    history = [
        log.p95_text_length
        for log in interval_statistics_logs
    ]

    # 마지막 chunk 의 개수가 너무 적으면 noise 에 민감해지므로, chunk size 의 반 이상이 되지 않으면 마지막 chunk 와 병합
    min_last_chunk_size = max(statistics_chunk_size // 2, 1)

    # chunk 단위로 slicing
    chunks = [
        history[i: i+statistics_chunk_size]
        for i in range(0, len(history), statistics_chunk_size)
    ]

    # 마지막 chunk (trend) 가 너무 작다면 마지막 chunk 와 병합하여 분석
    last_chunk_size = len(chunks[-1])
    if last_chunk_size < min_last_chunk_size:
        chunks[-2].extend(chunks[-1])
        chunks.pop()

    # 개별 chunk 의 평균값 계산
    avg_chunks = [
        float(np.mean(chunk))
        for chunk in chunks
    ]

    # 가중 선형 회귀 계산
    x = np.arange(len(avg_chunks))
    y = np.array(avg_chunks)

    # 최근 chunk 일수록 가중치 1씩 증가
    chunk_count = len(avg_chunks)
    weights = np.arange(1, chunk_count+1)

    # 기울기, 절편
    slope, intercept = np.polyfit(
        x,
        y,
        deg=1,
        w=weights,
    )

    # ax + b 형태의 방정식에 현재 추출된 chunk 관련 값에 넣음
    # 마지막 chunk 의 개수에 따라 x 값을 연속적인 값으로 설정
    target_x = (
        chunk_count
        - 1
        + min(
            last_chunk_size / statistics_chunk_size,
            1.0,
        )
    )

    predicted = (slope * target_x) + intercept

    return max(1, round(predicted))


def calculate_optimal_memory_usage_ratio(
        inferred_logs: list[SentimentInferredLog],
        oom_logs: list[SentimentOOMFallbackLog],
        previous_memory_usage_ratio: float,
        min_memory_ratio: float,
        max_memory_ratio: float,
        growth_ratio_step: float,
) -> float:
    """
    감성 추론 성공 대비 OOM 발생 비율 기반 로직을 적용하여 memory usage ratio 값 추론

    주의 사항
    - 해당 메서드로 추론된 결과는 정밀한 데이터 분석 방식을 적용한 것이 아닌 단순 추론 값임을 염두

    동작 방식
    - 감성 추론 성공 대비 OOM 발생 비율을 이전 memory usage ratio 에 적용 후 반환
    - OOM 발생 횟수가 없다면 이전 memory usage ratio 에 step 만큼 합한 후 반환
    - 감성 추론 성공 횟수가 없거나 OOM 횟수가 성공 횟수보다 크다면 최솟값 반환

    :param inferred_logs: 감성 추론 성공 관련 로그 list[SentimentInferredLog]
    :param oom_logs: 감성 추론 OOM 실패 관련 로그 list[SentimentOOMFallbackLog]
    :param previous_memory_usage_ratio: 이전에 설정된 memory usage ratio float
    :param min_memory_ratio: memory usage ratio 의 최솟값 float
    :param max_memory_ratio: memory usage ratio 의 최댓값 float
    :param growth_ratio_step: memory usage ratio 증가 시 더해줄 step float
    :return: 감성 추론 성공 대비 OOM 발생 비율 기반 로직을 적용하여 추론된 memory usage ratio float
    """

    inferred_logs_length = len(inferred_logs)
    oom_logs_length = len(oom_logs)

    if oom_logs_length == 0:
        return min(max_memory_ratio, previous_memory_usage_ratio + growth_ratio_step)

    if (
            inferred_logs_length == 0
            or oom_logs_length >= inferred_logs_length
    ):
        return min_memory_ratio

    return max(
        min_memory_ratio,
        previous_memory_usage_ratio * (1 - (oom_logs_length / inferred_logs_length))
    )


def _calculate_ema(
        ema_alpha: float,
        previous_value: Union[int, float],
        current_value: Union[int, float],
        min_ema_alpha: float,
        max_ema_alpha: float,
) -> Union[int, float]:
    """
    EMA (지수 이동 평균) 을 계산 후 반환

    주의 사항
    - alpha 값의 범위가 min/max 사이가 아닐 경우 이전 값을 반환

    :param ema_alpha: 적용 대상 EMA alpha float
    :param previous_value: 연산 대상 이전 값 Union[int, float]
    :param current_value: 연산 대상 현재 값 Union[int, float]
    :param min_ema_alpha: 검증 최솟값 EMA alpha float
    :param max_ema_alpha: 검증 최댓값 EMA alpha float
    :return: EMA 계산 값 float
    """

    if not (min_ema_alpha < ema_alpha < max_ema_alpha):
        return previous_value

    return ema_alpha * current_value + (1-ema_alpha) * previous_value


def _calculate_adaptive_ema_alpha(
        statistics_history: list[Union[float, int]],
        previous_ema_alpha: float,
        min_ema_alpha: float,
        max_ema_alpha: float,
        ema_alpha_step: float,
        ema_alpha_noise_threshold: float,
        min_threshold: int = 3,
) -> float:
    """
    이전 통계 기록 기반,
    EMA alpha (지수 이동 평균에서 과거 데이터의 가중치 값) 의 증가/감소 적용 후 반환

    int/float 숫자로 구성된 통계 history list 와 이전 ema 를 받아
    통계 추이와 증가/감소량 분석 기반, 현재 적용될 ema alpha 값을 반환

    주의 사항
    - statistics_history 는 예전 기록부터 최근 기록까지 오름차순 정렬되어 있는 기록임을 전제
    - 해당 메서드는 기본적으로 token length 의 percentile 추측을 위한 간이 메서드이며,
      따라서 분석 로직과 값이 정확하지 않음을 전제하고,
      설정값 혹은 비율 등은 해당 클래스 내부에서 개발자 임의로 설정된 값임을 주의

    동작 방식
    - 파라미터 min threshold 를 분석 최소치 및 최근 추세로 판단할 개수로 활용
    - min threshold 개수 이전, 과거 데이터들의 증가/감소량 평균과
      min threshold 개수만큼의, 최근 데이터들의 증가/감소량 평균을 계산
    - ema alpha noise threshold 보다 추이가 클 경우, 증가/감소에 따라 ema 값을 수정하여 반환

    :param statistics_history: 분석 대상 과거 통계 데이터 list[Union[float, int]]
    :param previous_ema_alpha: 분석 대상 과거 통계 데이터 중 가장 마지막으로 쓰인 ema alpha 값 float
    :param min_ema_alpha: ema alpha 하한선 float
    :param max_ema_alpha: ema alpha 상한선 float
    :param ema_alpha_step: ema alpha 증가/감소량 float
    :param ema_alpha_noise_threshold: ema alpha 증가/감소 정도의 무시 상한선 float
    :param min_threshold: 분석 대상 개수 최소치 및 최근 데이터들의 기준 개수 int
    :return 분석 및 결과 적용된 ema alpha 값 float
    """

    # 검증
    if len(statistics_history) <= min_threshold:
        return previous_ema_alpha

    # min_threshold 이전까지의 증가/감소량 기울기 평균
    history_deltas = [
        statistics_history[i+1] - statistics_history[i]
        for i in range(len(statistics_history) - min_threshold)
    ]
    avg_history_delta = np.mean(history_deltas)

    # min_threshold 개 만큼의 최근 증가/감소량 기울기 평균
    recent_delta = [
        statistics_history[i+1] - statistics_history[i]
        for i in range(len(statistics_history) - min_threshold, len(statistics_history))
    ]
    avg_recent_delta = np.mean(recent_delta)

    # 기울기 차이에 따라 상이 결과 반영
    delta_diff = avg_recent_delta - avg_history_delta

    # 최근 변동량 기울기 비율이 미미한 경우 가장 최근의 alpha 값 반환
    if abs(delta_diff) < ema_alpha_noise_threshold:
        return previous_ema_alpha

    # 증가 추세
    if delta_diff > 0:
        return min(max_ema_alpha, previous_ema_alpha + ema_alpha_step)
    # 감소 추세
    else:
        return max(min_ema_alpha, previous_ema_alpha - ema_alpha_step)