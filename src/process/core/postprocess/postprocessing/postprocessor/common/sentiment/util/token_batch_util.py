"""
token_batch_util.py
-------------------

감성 추론 모델 및 과정의 token, batch 관련 util 모듈
"""


import logging
import statistics
import time
from typing import List, Final

import torch

from transformers import (
    PreTrainedModel,
    PreTrainedTokenizer,
)

from util.logging_util import run_with_logging
from util.runtime_environment_util import get_available_inference_device, synchronize_inference_device, \
    clear_inference_device_cache, is_inference_oom_exception


# util 내부에서 공통 사용될 worst case dummy data
_DUMMY_DATA: Final[str] = "이것은실제환경의부하테스트를위해토큰화가많이일어나는한글로빽빽하게적은더미데이터문자열입니다"


def _build_mock_dummy_data(text_length: int) -> str:
    """
    해당 util 모듈 내부에서 사용되며, 
    내부 상수 _DUMMY_DATA 를 text length 만큼 증감하여 반환

    :param text_length: 필요한 글자수 int
    :return: text_length 만큼 증감된 _DUMMY_DATA str
    """

    dummy_str = _DUMMY_DATA.strip()
    return (dummy_str * (text_length // len(dummy_str) + 1))[:text_length]


def calculate_token_count_by_text_length(
        tokenizer: PreTrainedTokenizer,
        text_length: int,
) -> int:
    """
    글자 수에서 토큰 수를 역산 후 반환

    연산에 사용하는 dummy data 는 worst case 를 전제하여
    토큰 압축 및 분할이 어려운, 가득 찬 한글 데이터를 기준함

    :param tokenizer: 연산에 사용될 PreTrainedTokenizer
    :param text_length: 역산 대상 글자 수 int
    :return: 글자 수에서 역산된 토큰 수 int
    """

    return len(
        tokenizer(
            _build_mock_dummy_data(text_length),
            truncation=True,
            add_special_tokens=True,
        )["input_ids"]
    )


@run_with_logging()
def calculate_optimal_token_count_per_batch(
        model: PreTrainedModel,
        tokenizer: PreTrainedTokenizer,
        max_text_length: int,
        max_token_count_per_batch: int,
        measure_count: int,
        min_throughput_improvement_ratio: float,
) -> int:
    """
    환경/호스트 머신 기준 최적 token size per batch 계산하여 반환

    네트워크 혼잡 제어의 Slow Start 방식을 차용,
    하나의 batch 가 가질 수 있는 token 개수를 2 배씩 증가시키며 각 token 개수의 throughput 을 측정 후,
    현재 환경/호스트 머신 기준 최적의 token size per batch 값을 반환
    
    반환되는 값은 하나의 batch 에 들어갈 수 있는 원소의 개수가 아닌
    padding 을 포함한 총 token 개수를 의미함
    (padding 은 batch 에 들어가는 데이터 list 중 가장 긴 데이터의 길이로 맞춰짐)

    min_throughput_improvement_ratio 의 경우 throughput 의 유의미한 증가율을 의미함
    (throughput 증가율이 미세한 차이라면, 메모리 사용을 아끼기 위해 포기)

    주의 사항
    - warm up 과정 및 slow start 과정이 큰 오버헤더를 유발하므로,
      애플리케이션 setup 혹은 감성 추론 모델 객체 최초 생성 단계에서 1회만 실행 권장
    - 해당 연산 값은 max_text_length 길이의 dummy data 토큰 수를 기준한 것이므로,
      model 의 inference 과정에서도 tokenizer 의 max_length 설정값을 반드시 같은 토큰 개수만큼의 글자 수로 맞춰야 함

    :param model: transformers 감성 추론 모델 PreTrainedModel
    :param tokenizer: transformers model 이 적용된 tokenizer PreTrainedTokenizer
    :param max_text_length: batch 대상 개별 원소 문자열의 최대 허용 길이 int
    :param max_token_count_per_batch: batch 당 가질 수 있는 token 개수 연산에서의 상한선 int
    :param measure_count: 평균값 측정을 위한 throughput 측정 반복 횟수 int
    :param min_throughput_improvement_ratio: 최적 효율을 위한 throughput 증가율의 최솟값 float
    :return: 최적 batch size int
    """

    # 측정을 위한 값 추출
    token_count_per_text = calculate_token_count_by_text_length(
        tokenizer=tokenizer,
        text_length=max_text_length,
    )

    # 현재 호스트 머신이 지원하는 CPU/GPU 정보 추출 및 model 에 해당 자원 부여
    device = get_available_inference_device()
    model.to(device)

    # 측정 로직
    current_token_count = token_count_per_text
    best_token_count_per_batch = token_count_per_text

    batch_size = 1
    previous_throughput = None

    dummy_data = _build_mock_dummy_data(max_text_length)

    logging.info(f"[START] device={device}: Calculate optimal token count per batch")
    
    while True:
        try:
            # tokenizer
            encoded_inputs = tokenizer(
                [dummy_data] * batch_size,
                return_tensors="pt",
                truncation=True,
                padding=True,
                max_length=token_count_per_text,
                add_special_tokens=True,
            )

            current_token_count = encoded_inputs["input_ids"].numel()

            # 상한선 토큰 개수 검사
            if current_token_count > max_token_count_per_batch:
                break

            encoded_inputs = {
                key: value.to(device)
                for key, value in encoded_inputs.items()
            }

            # GPU warmup (실행 & 종료 동기화)
            with torch.no_grad():
                _ = model(**encoded_inputs)
            synchronize_inference_device(device)

            # 실질적 성능 (throughput) 측정
            latencies: List[float] = []

            # 외부 요인을 고려하여 여러 번 실행 후 평균값 측정
            for _ in range(measure_count):
                start_time = time.perf_counter()

                with torch.no_grad():
                    _ = model(**encoded_inputs)
                synchronize_inference_device(device)

                end_time = time.perf_counter()

                latencies.append(end_time - start_time)

            # 평균 값 측정
            average_latency = statistics.mean(latencies)

            # throughput (초당 처리량)
            current_throughput = current_token_count / average_latency

            logging.debug(
                f"[MEASURE] device={device}, "
                f"token_count={current_token_count}, "
                f"average_latency={average_latency:.6f}s, "
                f"throughput={current_throughput:.2f} tokens/sec"
            )

            # 첫 측정 제외
            if previous_throughput is not None:
                throughput_growth_ratio = current_throughput / previous_throughput

                # throughput 의 증가 효율이 최소 ratio 보다 작아지면 종료
                if throughput_growth_ratio < min_throughput_improvement_ratio:
                    logging.debug(
                        f"[STOP] device={device}, "
                        f"token_count={current_token_count}, "
                        f"Throughput is not improving effectively"
                    )
                    break

            # slow start (2배씩 batch 크기 증가)
            best_token_count_per_batch = current_token_count
            
            # 다음 루프를 위한 변수 세팅
            previous_throughput = current_throughput
            batch_size *= 2

        except Exception as e:
            if is_inference_oom_exception(e, device):
                logging.warning(
                    f"[FAILED] device={device}, token_count={current_token_count}, error={e}: "
                    f"Detected Out-Of-Memory error while calculating optimal batch size"
                )
                break

            logging.exception(
                f"[ERROR] token_count={current_token_count}, error={e}: "
                f"Detected unexpected error while calculating optimal batch size"
            )
            break

    logging.info(
        f"[END] best_token_count_per_batch={best_token_count_per_batch}: Calculate optimal token count per batch"
    )

    # 연산에 쓰인 자원 반납
    clear_inference_device_cache(device)

    return best_token_count_per_batch
