"""
runtime_environment_util.py
---------------------------

애플리케이션 실행 환경/호스트 머신 정보 관련 util 모듈
"""


import gc
import logging
from multiprocessing import cpu_count
from typing import Optional

import psutil
import numpy as np
import torch
from transformers import PreTrainedModel

from process.core.postprocess.postprocessing.postprocessor.common.sentiment.model.device_memory_snapshot import \
    DeviceMemorySnapshot
from process.core.postprocess.postprocessing.postprocessor.common.sentiment.type.device_types import DeviceType
from process.core.postprocess.postprocessing.postprocessor.common.sentiment.type.memory_types import \
    MemoryMeasurementConfidenceType, MemoryMeasurementMethodType


def get_recommended_workers_count() -> int:
    """
    현재 환경에서의 추천 cpu-bound 스레드 수 반환

    현재 환경의 cpu 개수 - 1 로 계산 후 반환
    단, 최소 1 값을 보장

    :return: 해당 환경에서의 추천 스레드 수 (cpu 개수 - 1) int
    """

    return max((cpu_count() or 1) - 1, 1)


def get_available_inference_device() -> torch.device:
    """
    현재 호스트 머신이 지원하는, 추론 과정에 활용할 자원 (CPU/GPU) 을 우선 순위에 따라 탐색

    본 메서드는 inference model 의 추론에 활용될 자원 탐색을 목적으로 활용되며,
    따라서 목적에 맞는 우선 순위로 지원 자원 device 를 반환함

    우선 순위
    - GPU
        - NVIDIA (cuda)
        - APPLE (mps)
        - INTEL (xpu)
    - CPU

    참고 사항
    - APPLE, INTEL GPU 의 경우, PyTorch 버전에 따라 지원 여부가 달라질 수 있어
      추가적인 조건문이 필요함
    - 설정된 우선 순위와 맞지 않게, 제조 버전에 따라 CPU 가 GPU 보다 좋은 성능을 내는 경우도 있으나,
      일반적인 기준 우선 순위를 전제함

    :return: 현재 호스트 머신이 지원하는, 추론 과정에 활용할 우선 순위에 따른 자원 torch.device
    """

    # GPU
    # NVIDIA (cuda)
    if torch.cuda.is_available():
        return torch.device(DeviceType.CUDA)

    # APPLE (mps)
    if (
            hasattr(torch, "backends")
            and hasattr(torch.backends, DeviceType.MPS)
            and torch.backends.mps.is_available()
    ):
        return torch.device(DeviceType.MPS)

    # INTEL (xpu)
    if (
            hasattr(torch, DeviceType.XPU)
            and torch.xpu.is_available()
    ):
        return torch.device(DeviceType.XPU)

    # CPU (fallback)
    return torch.device(DeviceType.CPU)


def synchronize_inference_device(device: torch.device) -> None:
    """
    torch device 의 CPU/GPU 연산 동기화

    GPU 는 비동기적으로 수행되기에 CPU 와 연산 타이밍이 달라질 수 있으므로
    둘의 연산 시점을 동기화하여 모두 종료될 때까지 대기

    해당 메서드는 latency, throughput 등의 정밀한 측정에서 주로 활용

    참고 사항
    - APPLE, INTEL GPU 의 경우, PyTorch 버전에 따라 지원 여부가 달라질 수 있어
      추가적인 조건문이 필요함

    - 일반적으로 CPU 의 RAM 과 GPU 의 VRAM 이 분리되어 있는 환경과 달리,
      APPLE silicon 맥북의 경우 둘의 메모리를 공유하여
      명시적인 synchronize 가 요구되지 않을 수 있음

    :param device: 동기화 대상 추론 자원 torch.device
    :return: 없음
    """

    device_type = device.type

    # NVIDIA (cuda)
    if device_type == DeviceType.CUDA:
        torch.cuda.synchronize()
        return

    # APPLE (mps)
    if device_type == DeviceType.MPS:
        # Apple MPS의 경우 현재 PyTorch 버전 기준 전역 동기화 API를 명시하거나 생략 가능
        if hasattr(torch, DeviceType.MPS) and hasattr(torch.mps, "synchronize"):
            torch.mps.synchronize()
        return

    # INTEL (xpu)
    if device_type == DeviceType.XPU:
        if hasattr(torch, DeviceType.XPU) and hasattr(torch.xpu, "synchronize"):
            torch.xpu.synchronize()
        return

    return


def clear_inference_device_cache(device: torch.device) -> None:
    """
    torch device cache, 메모리 정리 및 자원 반환

    주의 사항
    - CPU 는 gc.collect() 만 수행
    - GPU 의 경우 자원 반납에 많은 오버헤드가 발생하므로
      inference model 의 연산 종료 시점 혹은 fallback 에서만 활용하길 권고
    - 방어 코드를 위해 내부에서 device 에 맞는 synchronize 수행

    참고 사항
    - APPLE, INTEL GPU 의 경우, PyTorch 버전에 따라 지원 여부가 달라질 수 있어
      추가적인 조건문이 필요함

    :param device: 메모리 정리 대상 torch.device
    :return: 없음
    """

    # CPU/GPU 공통 가비지 컬렉션 수행
    gc.collect()

    # synchronize
    synchronize_inference_device(device)

    device_type = device.type

    # NVIDIA (cuda)
    if device_type == DeviceType.CUDA:
        torch.cuda.empty_cache()
        return

    # APPLE (mps)
    if device_type == DeviceType.MPS:
        if hasattr(torch, DeviceType.MPS) and hasattr(torch.mps, "empty_cache"):
            torch.mps.empty_cache()
        return

    # INTEL (xpu)
    if device_type == DeviceType.XPU:
        if hasattr(torch, DeviceType.XPU) and hasattr(torch.xpu, "empty_cache"):
            torch.xpu.empty_cache()
        return


def is_inference_oom_exception(exception: Exception, device: torch.device) -> bool:
    """
    대상 exception 이 model 의 inference 과정 중 발생한 OOM (Out-Of-Memory) exception 인지 판별

    model 의 inference OOM 은 RuntimeError 임을 전제로
    device 별 다른 조건으로 판별하며,
    단순 RuntimeError 일 경우 False 반환

    :param exception: 발생한 예외 객체 Exception
    :param device: 호출부 로직에서 활용 중인 대상 torch.device
    :return: OOM 여부 bool
    """

    device_type = device.type

    # CPU
    if device_type == DeviceType.CPU:
        # 메모리 관련 에러는 모든 case 를 방어하기 힘들어 임시 조건 부여
        # 단, 에러 메세지를 통한 문자열 검증을 맹신하지 않아야 함
        return (
                isinstance(exception, MemoryError)
                or isinstance(exception, RuntimeError) and "out of memory" in str(exception).lower()
        )

    # NVIDIA (cuda)
    if device_type == DeviceType.CUDA:
        return isinstance(exception, torch.cuda.OutOfMemoryError)

    # APPLE (mps)
    if device_type == DeviceType.MPS:
        # PyTorch 2.4+ 공식 최신 예외 클래스 검사
        if hasattr(torch, DeviceType.MPS) and hasattr(torch.mps, "OutOfMemoryError"):
            if isinstance(exception, torch.mps.OutOfMemoryError):
                return True

        # 구버전 맥북용 예외 클래스 검사
        if hasattr(torch, "backends") and hasattr(torch.backends, DeviceType.MPS):
            mps_backend = getattr(torch.backends, DeviceType.MPS)

            if hasattr(mps_backend, "MPSBackendError"):
                mps_error_class = getattr(mps_backend, "MPSBackendError")

                if isinstance(exception, mps_error_class):
                    return True

    # INTEL (xpu)
    if device_type == DeviceType.XPU:
        if hasattr(torch, DeviceType.XPU) and hasattr(torch.xpu, "OutOfMemoryError"):
            return isinstance(exception, torch.xpu.OutOfMemoryError)

    return False


def get_device_memory_snapshot(
        device: torch.device,
) -> DeviceMemorySnapshot:
    """
    현 시점 runtime 환경 기준 감성 추론 활용 device 별 메모리 상태 반환

    해당 메서드 호출 시점의 메모리 상태 정보를 DeviceMemorySnapshot 에 담아 반환하며,
    device 별 남은 메모리 양을 계산하는 로직의 정확도가 보장되지 않는 경우가 있으므로,
    호출부는 반드시 DeviceMemorySnapshot 내부 정보를 확인하고 로직을 작성하길 권고

    :param device: 감성 추론 모델이 동작하는 자원 대상 torch.device
    :return: 현 시짐 runtime 환경에서의 메모리 상태 정보 DeviceMemorySnapshot
    """

    device_type = device.type

    # NVIDIA (cuda)
    if device_type == DeviceType.CUDA:
        # 멀티 GPU 환경이 아니므로, index 가 지정되지 않았다면 cuda 중 물리적인 첫 번째 GPU 칩을 가져오도록 fallback
        device_index = device.index or 0

        # 외부 요인 (드라이버 버전, OS 등) 에 의한 메서드 호출 실패 방어
        try:
            # cuda 기준, 해당 GPU 칩의 빈 메모리 양, 총 메모리 양 (Byte 기준) 추출
            free_memory, total_memory = torch.cuda.mem_get_info(device_index)

            return DeviceMemorySnapshot(
                device_type=DeviceType.CUDA,
                available_memory_bytes=free_memory,
                memory_measurement_confidence=MemoryMeasurementConfidenceType.EXACT,
                memory_measurement_method=MemoryMeasurementMethodType.CUDA_API,
            )

        # fallback
        except Exception as e:
            logging.warning(
                f"[FAILED] process=torch.cuda.mem_get_info, device_index={device_index}: {str(e)}"
            )

            # PyTorch 가 수집한 hardware 스펙에서 총 메모리 양 추출
            total_memory = torch.cuda.get_device_properties(
                device_index
            ).total_memory

            # PyTorch 가 원활한 AI 연산을 위해 GPU 코드 호출 순간 미리 할당하여 가져간 메모리 (memory_reserved()) 와
            # AI 연산 관련 데이터가 들어 있는, 실제 사용 중인 공간 (memory_allocated()) 중 큰 값 기준으로 계산
            # 논리적으로 통상 reserved >= allocated 를 만족하지만, 내부 버그 혹은 그래픽 연산에 의해 다른 결과가 나올 수 있음
            used_memory = max(
                torch.cuda.memory_reserved(device_index),
                torch.cuda.memory_allocated(device_index),
            )

            free_memory = total_memory - used_memory

            return DeviceMemorySnapshot(
                device_type=DeviceType.CUDA,
                available_memory_bytes=free_memory,
                memory_measurement_confidence=MemoryMeasurementConfidenceType.ESTIMATED,
                memory_measurement_method=MemoryMeasurementMethodType.CUDA_API,
            )

    # APPLE (mps)
    elif device_type == DeviceType.MPS:
        # APPLE silicon 맥북의 경우 CPU/GPU 둘의 메모리를 공유하기 때문에
        # psutil 을 통해 간단히 현재 메모리의 남은 자원을 알아내어 추론할 수 있음
        # 구 버전 맥북의 경우 CPU/GPU 통합이 아닐 수 있으나, 파라미터 device 를 추론하는 코드에서 silicon 으로 한정
        # 단, CPU/GPU 통합이면서, 맥북의 GPU 관리 방식은 엄격하므로, 남은 용량의 60% 를 반환하는 안전 장치 부여
        free_memory = int(psutil.virtual_memory().available)

        return DeviceMemorySnapshot(
            device_type=DeviceType.MPS,
            available_memory_bytes=free_memory,
            memory_measurement_confidence=MemoryMeasurementConfidenceType.ESTIMATED,
            memory_measurement_method=MemoryMeasurementMethodType.PSUTIL,
        )

    # INTEL (xpu)
    elif device_type == DeviceType.XPU:
        device_index = None

        # xpu 는 라이브러리 지원이 완벽하지 못하므로, 방어
        try:
            # 멀티 GPU 환경이 아니므로, index 가 지정되지 않았다면 xpu 중 물리적인 첫 번째 GPU 칩을 가져오도록 fallback
            device_index = device.index or 0

            # xpu 기준, 해당 GPU 칩의 빈 메모리 양, 총 메모리 양 (Byte 기준) 추출
            free_memory, _ = torch.xpu.memory.mem_get_info(device_index)

            return DeviceMemorySnapshot(
                device_type=DeviceType.XPU,
                available_memory_bytes=free_memory,
                memory_measurement_confidence=MemoryMeasurementConfidenceType.EXACT,
                memory_measurement_method=MemoryMeasurementMethodType.XPU_API,
            )

        # fallback
        except Exception as e:
            logging.warning(
                f"[FAILED] process=torch.xpu.memory.mem_get_info, device_index={device_index}: {str(e)}"
            )

            # conservative fallback (6GB)
            # xpu 의 경우 라이브러리의 지원이 약하고 드라이버 버전에 따라 지원되는 메서드/정보가 다르기 때문에
            # 모든 경우를 방어할 수 없어 보수적인 값 (INTEL 의 그래픽카드 Arc 의 최하위 모델 크기) 으로 fallback
            free_memory = 6 * (1024 ** 3)

            return DeviceMemorySnapshot(
                device_type=DeviceType.XPU,
                available_memory_bytes=free_memory,
                memory_measurement_confidence=MemoryMeasurementConfidenceType.UNAVAILABLE,
                memory_measurement_method=MemoryMeasurementMethodType.HARDCODED_DEFAULT,
            )

    # CPU
    else:
        # 단순 남은 RAM 용량 반환
        # CPU 연산이기 때문에 OS 의 swap 등의 처리를 믿고 남은 전체 RAM 공간 반환
        free_memory = psutil.virtual_memory().available

        return DeviceMemorySnapshot(
            device_type=DeviceType.CPU,
            available_memory_bytes=free_memory,
            memory_measurement_confidence=MemoryMeasurementConfidenceType.EXACT,
            memory_measurement_method=MemoryMeasurementMethodType.PSUTIL,
        )


def estimate_max_token_count_per_batch(
        model: PreTrainedModel,
        device: torch.device,
        memory_usage_ratio: float,
) -> int:
    """
    현재 runtime 환경 기준 안전한 max token count per batch 상한선을 추정하여 반환

    해당 메서드는 device 별 현 시점에 남은 메모리 및 리소스 자원을 전제로
    model 연산 중 하나의 batch 에 최대 몇 개의 token 이 들어갈 수 있을지를 추정함

    해당 메서드에서 신경망 연산에 필요한 메모리 계산 로직은
    worst case 인 'batch 에 하나의 긴 문장 (estimated token 개수만큼의)' 이 들어왔을 때 기준 Attention memory 이므로,
    실제 batch 에 짧은 문장이 여러 개 들어갈수록 실사용 memory 는 줄어듦

    다음과 같은 상황에서 활용하길 권고
    - setup 시 slow start 의 초기 상한선
    - runtime OOM 발생 시 fallback batch 재조정
    - dynamic token bucket upper bound 계산

    주의 사항
    - 대략적인 연산을 통한 추정치일 뿐, 완벽한 상태를 고려한 반환값이 아님을 주의
    - 환경/호스트 머신/시점별 결과가 달라질 수 있음
    - 해당 반환 값을 기준으로 batch 를 구성할 때, 반드시 개별 원소의 토큰 개수와 최대 크기 (padding) 를 고려하여 연산해야 함
    - 보수적인 안전 장치가 있으나, 해당 반환 값을 사용하는 호출부는 반드시 OOM 등 에러에 대한 방어 코드를 작성하길 권고

    :param model: transformers 감성 추론 모델 PreTrainedModel
    :param device: 감성 추론 모델이 동작하는 자원 대상 torch.device
    :param memory_usage_ratio: 추정된 usable memory 기준 실제 활용할 비율 (안전 장치) float
    :return: 현재 runtime 환경 기준 안전한 max token count per batch 상한선 추정값 int
    """

    # 현재 남은 메모리 추출 및 남은 용량의 % 를 로직에 사용하는 안전 장치 부여
    current_memory_snapshot = get_device_memory_snapshot(device)
    free_memory = current_memory_snapshot.available_memory_bytes
    usable_memory = free_memory * memory_usage_ratio

    # ======================== #
    # 신경망 연산에 필요한 값 추출  #
    # ======================== #

    # 개별 모델별로 개별 데이터를 관리하는 변수명이 다르기 때문에, RoBERTa 표준 및 hugging face 의 권고 사항에 맞는 변수명으로 추출
    # 만약 해당 변수명이 존재하지 않다면 호출부 model 적용 메서드의 fallback 처리/파라미터 ratio 를 믿고 적당히 보수적인 표준 값으로 설정
    config = model.config

    # 하나의 토큰이 가지는 벡터 길이 (len)
    hidden_size = getattr(config, "hidden_size", 1024)
    # 신경망 layer 개수
    num_layers = getattr(config, "num_hidden_layers", 24)

    # 부동소수점 표현 precision 에 따른 tensor element byte size
    # 모델별 정밀는 float16/bfloat16 을 쓰는 경우 반정밀도 (Half Precision), 더 큰 경우 단정밀도 (Full Precision) 으로
    # 표현할 수 있는 수의 범위 (더 많은 소숫점) 에 따라 각각 2 byte, 4 byte 의 크기를 가짐
    dtype_bytes = (
        2 if model.dtype in (
            torch.float16,
            torch.bfloat16,
        )
        else 4
    )

    # ================= #
    # 최적의 토큰 개수 연산 #
    # ================= #

    # 층마다 linear (토큰 개수 * hidden_size * dtype_bytes) / attention (토큰 개수^2 * dtype_bytes) 만큼의 공간이 필요하므로
    # 최종 공식은 num_layer * (linear + attention) = usable_memory
    # 이를 이차 방정식으로 치환, 근의 공식으로 최적의 토큰 개수 연산
    quadratic_coefficient = num_layers * dtype_bytes
    linear_coefficient = num_layers * hidden_size * dtype_bytes
    constant_term = -usable_memory

    estimated_token_count: Optional[int] = None

    # noinspection PyTypeChecker
    for root in np.roots([quadratic_coefficient, linear_coefficient, constant_term]):
        
        # 상수인 usable_memory 가 이항 되며 음수임이 보장되기 때문에, 두 근은 양수/음수 조합이 보장됨
        # 이때 선택되어야 하는 값은 실수이면서 양수인 값
        if np.isreal(root) and root.real > 0:
            estimated_token_count = int(root)
            break

    if estimated_token_count is None:
        logging.warning(
            f"[FAILED] "
            f"device={device}, "
            f"free_memory={free_memory / (1024 ** 2):.2f}MB, "
            f"usable_memory={usable_memory / (1024 ** 2):.2f}MB, "
            f"Failed to calculate optimal token count per batch based on current usable memory "
            f"- return 2048"
        )

        # fallback
        # GPU 가 최소한의 병렬 연산 효율을 내기 위한 min 값
        # 호출부에서 추가적인 OOM fallback 로직으로 방어해야 함
        return 2048

    logging.info(
        f"[SUCCESS] "
        f"device={device}, "
        f"free_memory={free_memory / (1024 ** 2):.2f}MB, "
        f"usable_memory={usable_memory / (1024 ** 2):.2f}MB, "
        f"estimated_token_count={estimated_token_count}: "
        f"Calculate optimal token count per batch based on current usable memory"
    )

    return estimated_token_count
