"""
environment.py
--------------

애플리케이션 실행 시점 구동 환경 판별 기준 정의 Enum 모듈
"""


from enum import Enum


class Environment(Enum):
    LOCAL = "local"
    DEPLOY = "deploy"
