"""
base_process_pipeline.py
------------------------

파이프라인 공통 속성 추상 클래스 설정 모듈

주의 사항
- 해당 파이프라인 추상화 클래스는 파이프라인 기본 정보 반환 및 4 개의 주요 파이프라인 생명주기와 실행 메서드만을 정의하며,
  개별 메서드의 세부 구현/생략 및 의존성/상태관리 방식은 구현체가 책임을 가짐
"""


from abc import ABC, abstractmethod

from domain.platform.platform import Platform


class BaseProcessPipeline(ABC):
    """
    파이프라인 공통 속성 추상 클래스

    파이프라인 기본 정보와 4 개의 주요 파이프라인 단계 및 전체 실행 메서드의 구현 강제

    해당 클래스를 상속하는 클래스가 config registry 를 필요로 한다면
    ConfigRegistryRequired 마커 클래스를 상속하여 구현되어야 함
    """

    @classmethod
    @abstractmethod
    def get_platform(cls) -> Platform:
        pass

    @abstractmethod
    def run_ingest(self) -> None:
        pass

    @abstractmethod
    def run_preprocess(self) -> None:
        pass

    @abstractmethod
    def run_postprocess(self) -> None:
        pass

    @abstractmethod
    def run_finalize(self) -> None:
        pass

    @abstractmethod
    def run_pipeline(self) -> None:
        """
        전체 파이프라인 실행

        호출부에선 전체 프로세스의 순차 실행을 위해 구현된 해당 메서드를 활용할 수 있으며,
        플랫폼별 구현체 및 환경에 따라 자유롭게 해당 메서드를 구현 가능

        주의 사항
        - 개별 파이프라인 로직 수행 중 발생하는 에러는 반드시 외부로 전파해야 하는 규칙을 따름
        """

        pass
