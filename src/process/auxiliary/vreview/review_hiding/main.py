"""
main.py
-------

review_hiding 의 실행부

개발 환경에서의 통합 테스트를 위한 수동 진입점 모듈이며,
하나의 대표 시나리오 조합 (environment: shopping mall - platform - export) 를
실제 데이터 기반으로 테스트 및 실행, 검증함
"""


from core.common.bootstrap import run_bootstrap
from domain.platform.platform import Platform
from factory.bootstrap.bootstrap_config import LOCAL_BOOTSTRAP_CONFIG
from factory.process.hiding.review_hiding_builder import build_vreview_review_hiding_config
from factory.config.registry.local import build_local_config_registry
from process.auxiliary.vreview.review_hiding.review_hiding import review_hiding


def main():
    # environment (local) setting
    run_bootstrap(LOCAL_BOOTSTRAP_CONFIG)
    local_config_registry = build_local_config_registry()

    # execution
    review_hiding(
        platform=Platform.ABLY,
        hiding_config=build_vreview_review_hiding_config(local_config_registry),
        target_review_ids=[],
    )


if __name__ == "__main__":
    main()
