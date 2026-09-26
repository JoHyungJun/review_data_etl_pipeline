"""
main.py
-------

프로젝트 애플리케이션의 실행 위치 (entry point)

주의 사항
- 애플리케이션은 환경에 따라 다른 bootstrap 및 실행 방식을 제공하며,
  따라서 반드시 환경별로 프로젝트 내부에 정의된 환경변수를 실행 시점에 주입하여야 함
"""


from entry.application import Application


def main() -> None:
    Application().run()


if __name__ == "__main__":
    main()