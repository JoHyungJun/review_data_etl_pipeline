"""
base_sentiment_jsonl_logger.py
------------------------------

감성 추론 관련 JSONL logging 및 로그 내용을 저장하는 logger 관련 공통 속성 클래스 설정 모듈
"""


import json
import logging
from pathlib import Path
from typing import Optional, Union

from core.base.log.base_storage_logger import BaseStorageLogger
from process.core.postprocess.postprocessing.postprocessor.common.sentiment.log.model.models import BaseSentimentLog
from util.jsonl_util import stream_lines_between_bytes_from_jsonl
from util.logging_util import logging_file_event, logging_error_event
from util.path_util import get_or_create_directory


class BaseSentimentJsonlLogger(BaseStorageLogger):
    """
    감성 추론 관련 JSONL logging 및 로그 내용을 저장하는 logger 관련 공통 속성 클래스 모듈

    해당 객체는 static 한 성격으로 별도의 객체 생성 없이 class method 로 활용할 수 있지만,
    관리하는 변수들의 초기화를 위해 반드시 한 번의 initialize() 호출이 요구됨

    해당 클래스를 상속하는 로그 관련 클래스는 logging 기반으로 동작해야 하며,
    initialize() 에 logging 객체 관련 초기화, 포맷터, 파일 핸들러 등의 과정이 명시되어야 함

    주의 사항
    - 클래스 내부에서 관리되는 LOGGER_NAME 은 클래스 선언 시점에 강제,
      STORAGE_PATH 정보는 initialize() 시점에서의 초기화를 강제
    """

    @classmethod
    def initialize(
            cls,
            storage_path: Union[Path, str],
    ) -> None:
        """
        클래스 내부에서 관리하는 변수 및 logging 객체에 대한 초기화 및 설정

        :param storage_path: 로그 파일을 저장할 경로 Union[Path, str]
        :return: 없음
        """

        # validate
        if cls.LOGGER_NAME is None:
            raise ValueError(
                f"{cls.__name__} 클래스의 내부에서 관리하는 필수 변수에 대한 초기화 및 설정이 이루어지지 않았습니다. "
                "코드를 확인해주세요."
            )

        cls.STORAGE_PATH = Path(storage_path)

        logger = logging.getLogger(cls.LOGGER_NAME)

        if logger.handlers:
            cls._logger = logger
            return

        # root logger 객체와 분리 및 설정 (별도의 logging 객체로, root logger 에게 이벤트 (로그) 를 전파하지 않음)
        logger.setLevel(logging.INFO)
        logger.propagate = False

        get_or_create_directory(
            full_path=cls.STORAGE_PATH.parent
        )

        # JSONL 파일 핸들러
        file_handler = logging.FileHandler(
            cls.STORAGE_PATH,
            encoding="utf-8"
        )

        # logger 설정
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter("%(message)s"))

        logger.addHandler(file_handler)

        cls._logger = logger


    @classmethod
    def write_log(cls, sentiment_log_model: BaseSentimentLog) -> None:
        """
        감성 추론 관련 로그 write

        파라미터로 들어온 BaseSentimentLog 객체를 직렬화 하여 로그 파일에 작성하며,
        로그 작성 경로는 해당 클래스에서 내부적으로 관리되는 경로를 활용

        :param sentiment_log_model: 감성 추론 로깅에서 사용되는 이벤트 성격 단위 데이터 객체 BaseSentimentLog
        """

        cls._validate_initialized()

        try:
            cls.get_logger().info(
                json.dumps(
                    sentiment_log_model.to_json_dict(),
                    ensure_ascii=False,
                )
            )
        except Exception as e:
            logging_error_event(
                exception_instance=e,
                log_message="While writing log file",
                log_metadata={
                    "source_class": cls.__name__,
                    "file_path": cls.STORAGE_PATH,
                },
            )


    @classmethod
    def read_logs_between_bytes(
            cls,
            start_byte: Optional[int] = None,
            end_byte: Optional[int] = None,
    ) -> tuple[list[BaseSentimentLog], int]:
        """
        감성 추론 관련 특정 byte 범위의 로그들 및 마지막으로 read 한 정상적인 log 의 end byte 반환

        파라미터 start byte offset 를 기준으로 순방향 탐색하며 만나는 전체 로그를 반환하며,
        로그 작성 경로는 해당 클래스에서 내부적으로 관리되는 경로를 활용

        파라미터 start byte 이 선언되지 않는다면
        기본값 0으로 가장 첫 줄의 로그부터 파일의 끝까지 전체 로그를 반환

        주의 사항
        - 로그 수집 혹은 파싱 과정에서 에러 발생 (파일 오염 등) 시 (빈 list, 0) 튜플 반환
        - start_byte offset 이 설정되지 않는 경우 자동으로 파일의 가장 처음 byte 로 지정
        - end_byte offset 이 설정되지 않는 경우 자동으로 로직 실행 최초 시점의 EOF (End-Of-File) byte 로 지정

        :param start_byte: read 대상 로그 파일의 시작 절대 위치 byte int
        :param end_byte: read 대상 로그 파일의 끝 절대 위치 byte int
        :return:
            tuple[
                offset 기준 감성 추론 관련 특정 byte 범위의 로그 list[BaseSentimentLog],
                마지막 성공적으로 read 한 해당 줄의 데이터 및 개행 문자 이후의 next cursor byte 위치 int,
            ]
        """

        cls._validate_initialized()

        if not cls.STORAGE_PATH.exists():
            logging_file_event(
                file_path=cls.STORAGE_PATH,
                log_prefix="LOAD",
                log_metadata={
                    "source_class": cls.__name__,
                    "process": "read_log_with_byte_offset",
                },
                log_message="File not found",
                log_level="warning",
            )
            return [], 0

        try:
            logs: list[BaseSentimentLog] = []
            current_cursor_byte = 0

            with stream_lines_between_bytes_from_jsonl(
                    file_path=cls.STORAGE_PATH,
                    start_byte=start_byte,
                    end_byte=end_byte
            ) as log_iterator:

                # read/write 가 동시에 일어났을 때, 마지막 줄은 파싱에 실패할 수밖에 없음. 이는 정상적인 케이스.
                # 단, 이는 마지막 줄에 대해서만 파싱 에러를 허용해야 하는데, 현재 줄이 마지막 줄임을 판단할 근거가 없으므로,
                # 루프의 최상단에서 '이전에 invalid line 이 있었는가' 를 검사하면 '마지막 줄이 아닌 줄에서 파싱 에러가 났음'을 검증 가능
                has_invalid_line = False
                for log_raw_line, end_of_line_byte in log_iterator:
                    if has_invalid_line:
                        raise ValueError(
                            f"{cls.STORAGE_PATH} 파일 파싱 중 jsonl 형식이 아닌 줄을 발견했습니다. "
                            f"데이터의 오염이 의심됩니다. 파일을 확인해주세요. "
                        )

                    try:
                        log_dict = json.loads(log_raw_line)
                        current_cursor_byte = end_of_line_byte
                    except json.JSONDecodeError:
                        has_invalid_line = True
                        continue

                    logs.append(BaseSentimentLog.from_dict(log_dict))

            return logs, current_cursor_byte

        except Exception as e:
            logging_error_event(
                exception_instance=e,
                log_message="Detected unexpected error while reading and parsing sentiment log",
                log_message_detail="return empty list",
                log_metadata={
                    "source_class": cls.__name__,
                    "process": "full_scan_log",
                    "error_message": str(e),
                },
            )
            return [], 0


    @classmethod
    def full_scan_logs(cls) -> tuple[list[BaseSentimentLog], int]:
        """
        감성 추론 관련 전체 로그들 및 마지막으로 read 한 정상적인 log 의 end byte 반환

        로그 작성 경로는 해당 클래스에서 내부적으로 관리되는 경로를 활용

        전체 로그 데이터를 애플리케이션 메모리에 올리지 않고 Iterator 방식으로 수집 후 반환

        주의 사항
        - 로그 수집 혹은 파싱 과정에서 에러 발생 (파일 오염 등) 시 (빈 list, 0) 튜플 반환

        :return:
            tuple[
                감성 추론 관련 전체 로그 list[BaseSentimentLog],
                마지막 성공적으로 읽은 줄의 끝 byte int,
            ]
        """

        return cls.read_logs_between_bytes()


    @classmethod
    def clear_logs(cls) -> None:
        """
        해당 클래스가 관리하는 로그 파일 내에 저장된 내용을 모두 지우고 초기화

        주의 사항
        - 해당 클래스가 관리하는 logger 객체에 대한 정보는 유지됨
        - 해당 메서드는 IO read/write 동시성 발생 시 심각한 오류를 유발할 수 있으므로,
          반드시 해당 메서드 활용 시에 lock 을 활용한 호출부에서의 활용을 강제

        :return: 없음
        """

        cls._validate_initialized()

        try:
            with open(cls.STORAGE_PATH, "w", encoding="utf-8"):
                cls.STORAGE_PATH.touch(exist_ok=True)

        except Exception as e:
            logging_error_event(
                exception_instance=e,
                log_message="While clearing sentiment log file",
                log_metadata={
                    "source_class": cls.__name__,
                    "file_path": cls.STORAGE_PATH,
                },
            )
            raise
