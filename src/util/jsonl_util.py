"""
jsonl_util.py
-------------

jsonl 데이터 포맷팅/추출/전처리 관련 util 모듈

주의 사항
- 특정 줄 접근, 수정, 파싱 등의 로직은 jsonl 의 특성을 고려하여
  관련 라이브러리 사용 혹은 개행 문자 ('\n') 를 기준으로 로직을 작성
"""


import json
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Union, Iterator

from util.logging_util import logging_file_event, logging_error_event


@contextmanager
def stream_lines_between_bytes_from_jsonl(
        file_path: Union[Path, str],
        start_byte: Optional[int] = None,
        end_byte: Optional[int] = None,
) -> Iterator[Iterator[tuple[str, int]]]:
    """
    jsonl 파일에서 시작 ~ 끝 위치 byte offset 기준에 위치한 데이터들에 대해
    yield 로 줄 단위 및 마지막 읽은 byte tuple 를 순차 반환하는 Iterator (context manager 객체) 를 반환

    해당 메서드는 context manager 객체를 반환하며,
    파일 관련 I/O 처리가 안정적으로 구현됨
    
    호출부는 해당 메서드의 Iterator 객체를 with 문 내에서 선언하여
    for 문 혹은 next() 를 통해 jsonl 파일의 한 줄씩 순차 반환 받을 수 있음

    주의 사항
    - 반환하는 Iterator 는 단순히 개행 문자 기준으로 줄을 반환하는 것이 아니며,
      개행 문자, 공백 등의 줄은 모두 무시한 후 실제 데이터가 적힌 줄의 시작 지점까지 도달한 후에 read 후 해당 줄을 반환
      (단, 해당 줄의 jsonl 포맷이 지켜졌는가에 대한 여부는 검증하지 않음)

    - 호출부는 해당 메서드가 반환하는 Iteration 객체를 활용할 때,
      I/O, StopIteration 등 해당 로직에 대해 발생할 수 있는 모든 에러의 책임을 지니며,
      파라미터와 jsonl 파일간의 정합성에 대해 발생할 수 있는 모든 에러의 책임 또한 지님

    - start_byte offset 이 설정되지 않는 경우 자동으로 파일의 가장 처음으로 지정됨

    - end_byte offset 이 설정되지 않는 경우 자동으로 로직 실행 최초 시점의 EOF (End-Of-File) byte 로 지정되며,
      이는 파일의 read 중 동시에 추가로 write 되는 데이터들은 무시하여 안정적인 데이터 반환의 목적

    - read/write 가 동시에 일어났을 때 작성이 완료되지 않은 불완전한 line 이 반환될 수 있으며,
      호출부는 이를 방어하는 로직을 반드시 작성하길 권고

    :param file_path: 대상 jsonl 파일 경로 Union[Path, str]
    :param start_byte: 탐색을 시작할 jsonl 파일의 시작 절대 byte 위치 Optional[int]
    :param end_byte: 탐색을 끝낼 jsonl 파일의 끝 절대 byte 위치 Optional[int]
    :return:
        jsonl 파일에 접근 및 load 하는 Iterator[
            tuple[
                개행 문자, 공백이 제거된 정상적인 데이터 줄 str,
                해당 줄의 데이터 및 개행 문자 이후의 next cursor byte 위치 int,
            ]
        ]
    """

    jsonl_file = None
    try:
        # byte 기준 read
        jsonl_file = open(file_path, "rb")

        # 파라미터 검증 및 정책에 따른 재할당
        if start_byte is None:
            start_byte = 0

        if end_byte is None:
            jsonl_file.seek(0, os.SEEK_END)
            end_byte = jsonl_file.tell()

        # 제네레이터 설정
        jsonl_file.seek(start_byte)

        def _generator():
            # EOF 에 도달한 경우 제네레이터는 b'' 를 반환
            binary_eof = b''

            while True:
                raw_line = jsonl_file.readline()

                if raw_line == binary_eof:
                    return

                # read 중 write 된 데이터는 버림
                # 문장의 끝이 아닌 next cursor 위치 추출
                cursor_byte = jsonl_file.tell()
                if cursor_byte > end_byte:
                    return

                line = raw_line.decode("utf-8").strip()

                # 개행 문자, 공백 줄 방어
                if not line:
                    continue

                yield line, cursor_byte

        yield _generator()

    finally:
        if jsonl_file and not jsonl_file.closed:
            jsonl_file.close()


def load_lines_before_byte_from_jsonl(
        file_path: Union[Path, str],
        end_byte: Optional[int] = None,
        load_line_count: int = 1,
        reverse_order: bool = True,
) -> Optional[list[dict]]:
    """
    jsonl 파일에서 줄의 끝 byte 위치 기준 역방향으로 위치한 객체 (줄) 를
    파라미터 load line count 개수만큼 추출하여 dict 형태로 파싱 후 반환

    end_byte 를 기준으로 역방향으로 chunk 단위 탐색을 수행하며,
    개행 문자 기준 하나의 객체 (한 줄) 를 판단 (연속된 개행 문자는 방어)

    따라서 end_byte 는 반드시 추출하고자 하는 객체 (줄) 의 끝 byte 위치, 객체의 끝 개행 문자 위치 등
    역방향 탐색의 시작 위치이어야 하며,

    탐색 중 연속되는 개행 문자가 있을 경우 해당 개행 문자로만 이루어진 줄은 무시하고,
    개행 문자가 아닌 실제 데이터만 load 대상으로 판단하여 반환

    주의 사항
    - 원칙적으로 end_byte 위치는 문장의 끝 글자의 위치 정보가 담겨야 하나,
      내부 방어 로직을 통해 연속된 개행 문자, EOF 등을 방어함

    - 파일 접근, 문법, 파싱 등 해당 로직 중에 발생하는 에러의 경우 에러 자체를 raise 하지 않고
      별도의 로그 처리 후 None 을 반환

    - 해당 로직은 엄밀한 jsonl 포맷 (한 줄에 하나의 데이터 + dict 형태의 데이터 포맷) 에 대해 개행 문자 기준 판별 로직이므로,
      이로 인해 발생할 수 있는 다음과 같은 논리적인 에러 및 문제는 호출부가 책임을 가지며, None 이 반환됨
        - 특정 줄, 혹은 파일 자체 데이터 jsonl 포맷이 깨진 경우
        - 특정 줄, 혹은 파일 전체 데이터가 오염 혹은 손상된 경우
        - 특정 줄 내부에 문자가 아닌 개행 문자가 들어간 경우
        - 파라미터 end_byte 위치가 특정 줄, 혹은 파일의 끝 위치가 아닐 경우

    - end_byte 파라미터가 None 일 경우 offset 은 파일의 마지막 위치로 지정

    - 해당 메서드는 항상 list 형태로 결과를 반영하며, load 중 에러 발생 같은 경우에만 None 반환

    - 반환되는 list 는 기본 값으로 역순으로 객체 (줄) 을 반환하며 (가장 마지막 줄이 반환 list 의 가장 첫 번째 index 에 위치),
      reverse_order 파라미터를 통해 순서 조정 가능

    - load_line_count 파라미터보다 적은 객체 (줄) 을 가진 파일의 경우 전체 파일 객체를 반환하며,
      따라서 반드시 파라미터 load_line_count 개수 만큼의 list 반환을 보장하지 않음

    :param file_path: 대상 jsonl 파일 경로 Union[Path, str]
    :param end_byte: 역방향 탐색을 시작할 jsonl 객체의 끝 절대 byte 위치 Optional[int]
    :param load_line_count: 추출할 객체 (줄) 개수 int
    :param reverse_order: 반환 받을 list 의 순서 bool
    :return: 줄의 끝 byte 위치 기준 줄의 객체를 파싱한 Optional[list[dict]]
    """

    try:
        # validate
        if load_line_count <= 0:
            raise ValueError("파라미터인 load_line_count 는 1 이상의 값이어야 합니다. 코드를 확인해주세요.")

        offset_byte_size = 1

        with open(file_path, "rb") as file:

            file.seek(0, os.SEEK_END)
            file_size = file.tell()

            if file_size == 0:
                raise ValueError("파라미터인 file_path 의 파일이 비어 있습니다. 파일을 확인해주세요.")

            if end_byte is not None:
                # 파라미터로 EOF 기준 위치가 들어왔을 경우 보정
                if end_byte == file_size:
                    end_byte -= offset_byte_size

                if end_byte < 0 or end_byte >= file_size:
                    raise ValueError(
                        f"파라미터인 end_byte 가 해당 파일의 최소/최대 byte 위치 값을 벗어났습니다. "
                        f"파라미터를 확인해주세요. : 기댓값: 0 ~ {file_size}"
                    )
                base_byte = end_byte
            else:
                file.seek(0, os.SEEK_END)
                base_byte = file.tell() - offset_byte_size

            if base_byte < 0:
                raise ValueError("주어진 offset 이전의 추출 가능 데이터가 존재하지 않습니다. 파일 혹은 로그를 확인해주세요.")

            # 시작 지점 byte 로부터 역순으로 연속된 개행 문자를 제외한, 실제 데이터가 담긴 줄의 끝 byte 추출
            result_dicts = []

            buffer_byte_str = b""
            buffer_size = 4096  # 한 번에 읽을 버퍼 사이즈 기준은 4 KB

            newline_byte_str = b"\n"

            current_end_byte = base_byte

            # 파일에서 버퍼만큼 역순으로 load 후 개행문자 기준 line 검증
            while True:
                current_start_byte = max(0, current_end_byte - buffer_size)
                read_size = current_end_byte - current_start_byte + offset_byte_size

                # 다음 루프에 사용될 값 덮어쓰기
                current_end_byte = current_start_byte - offset_byte_size

                file.seek(current_start_byte, os.SEEK_SET)
                current_chunk = file.read(read_size)
                buffer_byte_str = current_chunk + buffer_byte_str

                if (
                        newline_byte_str not in buffer_byte_str
                        and current_start_byte != 0
                ):
                    continue

                current_lines = buffer_byte_str.split(newline_byte_str)

                # 첫 번째를 제외한 원소의 파싱 과정에서 JSONDecodeError 가 났을 경우 파일 혹은 포맷 오염
                for current_line in reversed(current_lines[1:]):
                    current_line = current_line.rstrip(b'\r')

                    # 연속된 개행 문자 및 \r\n 케이스 방어
                    if not current_line:
                        continue

                    current_line_dict = json.loads(current_line)

                    # 데이터가 dict 가 아니라면 에러 반환
                    if not isinstance(current_line_dict, dict):
                        raise ValueError("각 줄의 데이터는 반드시 dict 형태로 구성되어야 합니다. 파일을 확인해주세요.")

                    result_dicts.append(current_line_dict)

                # chunk 에 의해 데이터가 중간에서 잘릴 가능성이 있는 건 논리적으로 첫 번째 원소 뿐
                splittable_line = current_lines[0]
                try:
                    available_dict = json.loads(splittable_line.rstrip(b'\r'))
                    
                    if not isinstance(available_dict, dict):
                        raise ValueError("각 줄의 데이터는 반드시 dict 형태로 구성되어야 합니다. 파일을 확인해주세요.")

                    result_dicts.append(available_dict)
                    buffer_byte_str = b""
                
                except json.JSONDecodeError:
                    if current_start_byte == 0:
                        raise

                    buffer_byte_str = splittable_line

                if len(result_dicts) >= load_line_count:
                    break

                if current_start_byte == 0:
                    break

        # formatting
        result_dicts = result_dicts[:load_line_count]

        if not reverse_order:
            result_dicts.reverse()

        return result_dicts

    # I/O 및 파일 관련 에러 및 논리적으로 발생 시킨 에러
    except (FileNotFoundError, PermissionError, IsADirectoryError, ValueError) as e:
        logging_file_event(
            file_path=file_path,
            log_prefix="LOAD",
            log_metadata={
                "process": "load_lines_before_offset_line_from_jsonl",
                "error_message": str(e),
            },
            log_message=f"Invalid path, file or data - return None",
            log_level="warning",
        )
        return None

    # 문법, 타입 등 파싱 관련 에러
    except (json.JSONDecodeError, KeyError, TypeError, UnicodeDecodeError) as e:
        logging_error_event(
            exception_instance=e,
            log_message="While parsing jsonl data - return None",
            log_message_detail=str(e),
            log_metadata={
                "process": "load_lines_before_offset_line_from_jsonl",
                "file_path": file_path,
            },
            log_prefix="PARSE",
        )
        return None

    # 그 외 에러
    except Exception as e:
        logging_error_event(
            exception_instance=e,
            log_message="Detected unexpected error while loading and parsing jsonl data",
            log_message_detail=str(e),
            log_metadata={
                "process": "load_lines_before_offset_line_from_jsonl",
                "file_path": file_path,
            },
        )
        return None
