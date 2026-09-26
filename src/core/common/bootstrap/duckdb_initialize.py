"""
duckdb_initialize.py
--------------------

애플리케이션 프로세스 실행에 요구되는 duck db 설정 관련 관련 초기화 및 setup 모듈
"""


import duckdb

from util.logging_util import logging_error_event


def initialize_duckdb() -> None:
    """
    애플리케이션 프로세스 실행에 요구되는 duck db 설정 관련 관련
    초기화 및 setup 모듈
    
    주요 역할
    - duckdb 연결 테스트
    - duckdb 환경에 Excel 패키지 설치

    :return: 없음
    """

    try:
        # duck db install excel package
        con = duckdb.connect()
        con.execute("INSTALL excel;")
        con.close()

    except Exception as e:
        logging_error_event(
            exception_instance=e,
            log_message="While initializing duck db",
            log_message_detail=str(e),
            log_metadata={
                "process": "initialize_duckdb",
            },
        )
        raise
