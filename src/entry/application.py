"""
application.py
--------------

애플리케이션 실행 관련 클래스 모듈

애플리케이션 실행 환경에 따라 다른 bootstrap 및 실행 방식을 정의
"""


from entry.deploy.deploy_application import DeployApplication
from entry.environment import Environment
from entry.local.local_application import LocalApplication
from util.runtime_environment_util import resolve_value_from_environment_variables


class Application:

    APP_ENV_ENVIRONMENT_KEY = "APP_ENV"

    def run(self) -> None:
        """
        환경변수에서 추출한 실행 환경에 따라 애플리케이션 실행
        """

        environment = resolve_value_from_environment_variables(self.APP_ENV_ENVIRONMENT_KEY)
        try:
            environment = Environment(environment)

        except ValueError:
            raise RuntimeError(
                f"프로젝트 내부에 선언되지 않은 환경변수 값입니다. 외부 환경변수를 확인해주세요. : {environment}"
            )

        # 환경별 분기
        if environment == Environment.LOCAL:
            LocalApplication().run()

        elif environment == Environment.DEPLOY:
            DeployApplication().run()
            pass

        else:
            raise RuntimeError(
                f"미구현 환경변수로 실행되었습니다. 코드를 확앤해주세요. : {environment}"
            )
