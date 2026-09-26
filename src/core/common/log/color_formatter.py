"""
color_formatter.py
------------------

로깅 관련 컬러 포맷터 정의 클래스 모듈
"""


import logging


class ColorFormatter(logging.Formatter):
    """
    로그용 컬러 포맷터 클래스

    로그 메세지 가시성을 위해 로그 레벨별로 개별 색상을 지정하고
    로그 메시지 본문은 기본 Formatter 결과 문자열에 컬러 코드를 감싸서 반환
    """

    COLORS = {
        'DEBUG': '\033[38;5;153m',
        'INFO': '\033[32m',
        'WARNING': '\033[33m',
        'ERROR': '\033[31m',
        'CRITICAL': '\033[41m',
    }
    RESET = '\033[0m'

    def format(self, record) -> str:
        """
        로그 레코드에 컬러 코드 적용 후 문자열 반환

        :param record: 로그 레코드 객체
        :return: 컬러가 적용된 최종 포맷 str
        """

        color = self.COLORS.get(record.levelname, self.RESET)
        message = super().format(record)

        return f"{color}{message}{self.RESET}"
