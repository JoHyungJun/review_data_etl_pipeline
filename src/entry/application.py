"""
application.py
--------------

애플리케이션 실행 관련 클래스 모듈

애플리케이션 실행 환경에 따라 다른 bootstrap 및 실행 방식을 정의
"""


import os

from entry.environment import Environment
from entry.runtime.local_application import LocalApplication


class Application:

    APP_ENVIRONMENT_KEY = "APP_ENV"

    def run(self) -> None:
        environment = self._resolve_environment()

        if environment == Environment.LOCAL:
            LocalApplication().run()

        elif environment == Environment.DEPLOYMENT:
            # TODO
            pass

        else:
            raise RuntimeError(
                f"미구현 환경변수로 실행되었습니다. 코드를 확앤해주세요. : {environment}"
            )


    def _resolve_environment(self) -> Environment:
        environment = os.getenv(self.APP_ENVIRONMENT_KEY)

        if environment is None:
            raise RuntimeError(
                f"{self.APP_ENVIRONMENT_KEY} 환경변수가 설정되지 않아 프로젝트 실행에 실패하였습니다. 외부 환경변수를 확인해주세요."
            )

        try:
            return Environment(environment)

        except ValueError:
            raise RuntimeError(
                f"프로젝트 내부에 선언되지 않은 환경변수 값입니다. 외부 환경변수를 확인해주세요. : {environment}"
            )
