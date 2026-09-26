"""
path_util.py
------------

디렉토리/파일 및 경로 관련 util 모듈
"""


import inspect
import logging
import os.path
import shutil
from pathlib import Path
from typing import Union, Optional, Any

from config.constant.common.name_constants import *
from src.util.datetime_util import get_validated_date_by_str


def get_root_directory() -> Path:
    """
    프로젝트 루트 디렉토리 (최상위 기준 경로 디렉토리) 경로 탐색 및 반환

    루트 디렉토리를 기준으로 하위 주요 디렉토리 및 파일 경로를 정의하기 위해 활용

    해당 메서드가 실행되는 파일 기준, 상위 디렉토리를 역순 탐색하여
    루트 디렉토리 하위에 존재하는, 해당 프로젝트 필수 디렉토리 (src, datas, sentiment_model, logs) 가
    모두 존재하는 디렉토리를 루트 디렉토리로 판단하고 반환

    :return: 프로젝트 루트 디렉토리 경로
    """

    current = Path(__file__).resolve()

    # 역순 탐색 및 현재 디렉토리에 필수 디렉토리가 모두 존재할 때 반환
    for parent in current.parents:
        if all(
                (parent / folder).exists()
                for folder in [
                    SRC_DIRECTORY_NAME,
                    DATAS_DIRECTORY_NAME,
                    SENTIMENT_MODEL_DIRECTORY_NAME,
                    LOGS_DIRECTORY_NAME,
                ]
        ):
            return parent

    raise RuntimeError("최상위 폴더를 찾을 수 없습니다. 프로젝트 구조를 다시 확인해주세요.")


def get_or_create_directory(
    base_path: Optional[Union[Path, str]] = None,
    directory_name: Optional[str] = None,
    full_path: Optional[Union[Path, str]] = None,
) -> Path:
    """
    탐색 경로의 디렉토리 경로를 반환하거나,
    해당 탐색 경로에 디렉토리가 존재하지 않는다면 해당 경로에 따른 디렉토리 생성 후 경로 반환

    파라미터엔 full_path / base_path + directory_name 두 조합 중 하나는 반드시 입력해야 하며,
    파라미터가 모두 설정 됐을 시 full_path 가 base_path + directory_name 보다 우선 순위를 가짐

    :param base_path: 기준 경로 (탐색 대상 최종 디렉토리 기준 부모 디렉토리) Optional[Union[Path, str]]
    :param directory_name: 탐색 대상 디렉토리명 str
    :param full_path: 탐색 대상 전체 경로 Optional[Union[Path, str]]
    :return: 존재하는 혹은 새로 생성된 디렉토리 전체 경로 Path
    """

    # full_path 파라미터가 우선 순위를 가짐
    if full_path is not None:
        if base_path is not None or directory_name is not None:
            logging.warning(f"[USE] base_path={base_path}, directory_name={directory_name}, full_path={full_path}: "
                            f"Both full_path and base_path/directory_name are provided - selected full_path")

        full_path = Path(full_path)

        # 경로에 대상 디렉토리가 존재하지 않는다면 생성
        if not full_path.exists():
            logging.warning(f"[MAKE] path={full_path}: Directory not found - create directory on this path")
            full_path.mkdir(parents=True, exist_ok=True)

        return full_path

    # full_path 가 파라미터로 전달되지 않았다면 base_path + directory_name 는 모두 None 일 수 없음
    if base_path is None or directory_name is None:
        raise ValueError("full_path 가 없을 경우 base_path 와 directory_name 은 모두 전달되어야 합니다.")

    directory_path = Path(base_path) / directory_name

    # 경로에 대상 디렉토리가 존재하지 않는다면 생성
    if not directory_path.exists():
        logging.warning(f"[MAKE] path={directory_path}: Directory not found - create directory on this path")
        directory_path.mkdir(parents=True, exist_ok=True)

    return directory_path


def get_period_directory_name(start_date: str, end_date: str) -> str:
    """
    "시작 날짜 ~ 종료 날짜" 포맷의 디렉토리명 반환

    스크래핑 데이터의 기간별 구분 시
    동일한 포맷의 이름을 개별 디렉토리에 부여하기 위해 활용
    
    파라미터의 start_date, end_date 는 "YYYY-MM-DD" 포맷 검증을 거침

    :param start_date: 시작 날짜 str
    :param end_date: 종료 날짜 str
    :return: 'YYYY-MM-DD ~ YYYY-MM-DD' 포맷의 str
    """

    return f"{get_validated_date_by_str(start_date)} ~ {get_validated_date_by_str(end_date)}"


def get_or_create_date_period_directory(
        start_date: str,
        end_date: str,
        base_path: Union[Path, str],
) -> Path:
    """
    기준 경로 + 기간별 포맷 명의 디렉토리 경로를 반환하거나,
    해당 탐색 경로에 디렉토리가 존재하지 않는다면 해당 경로에 기간별 포맷명의 디렉토리 생성 후 경로 반환

    :param start_date: 시작 날짜 str
    :param end_date: 종료 날짜 str
    :param base_path: 기준 경로 (탐색 대상 최종 디렉토리 기준 부모 디렉토리) Union[Path, str]
    :return: 존재하는 혹은 새로 생성된 '기준 경로 + 기간별 포맷명' 의 디렉토리 경로 Path
    """

    period_directory_name = get_period_directory_name(
        start_date=start_date,
        end_date=end_date,
    )

    return get_or_create_directory(base_path=Path(base_path), directory_name=period_directory_name)


def get_file_name_by_path(path: Union[Path, str]) -> str:
    """
    전체 파일 경로에서 파일명 추출 및 반환

    :param path: 전체 파일 경로
    :return: 파일명 str
    """
    
    return os.path.basename(Path(path))


def move_file_to_directory(
        file_path: Union[Path, str],
        target_directory_path: Union[Path, str],
) -> Path:
    """
    대상 경로 (file_path) 의 파일을 대상 디렉토리 경로 (target_directory_path) 로 이동 및
    이동된 대상 파일의 경로 반환

    해당 탐색 경로에 디렉토리가 존재하지 않는다면 해당 경로에 따른 디렉토리 생성

    :param file_path: 이동 대상 파일 경로
    :param target_directory_path: 이동할 디렉토리 경로
    :return: 이동된 파일의 최종 경로
    """

    file_path = Path(file_path)
    target_directory_path = Path(target_directory_path)

    # 경로에 대상 디렉토리가 존재하지 않는다면 생성, 존재한다면 무시
    target_directory_path.mkdir(parents=True, exist_ok=True)

    # 파일 이동
    shutil.move(str(file_path), str(target_directory_path))

    moved_file_path = target_directory_path / file_path.name
    return moved_file_path


def get_relative_path(target: Any) -> str:
    """
    파라미터로 들어온 대상 target 의 위치를
    프로젝트 root 디렉토리 기준, 상대 경로로 반환

    주의 사항
    - target 에는 메서드, 클래스, 모듈 등 다양한 대상이 들어올 수 있으나,
      built-in (str, list 등) 객체, 혹은 프로젝트 root 외부의 값이 들어올 경우
      상대 경로의 계산에서 에러가 발생하여, 기본 절대 경로 전체를 반환함

    :param target: 상대 경로 계산 대상 Any
    :return: 프로젝트 root 디렉토리 기준 대상의 상대 경로 str
    """

    # 전체 절대 경로
    full_path = Path(inspect.getfile(target))

    # 프로젝트 root 경로
    project_root_path = get_root_directory()

    # 프로젝트 root 경로로부터 상대 경로 추출
    try:
        relative_path = full_path.relative_to(project_root_path)
    except ValueError:
        relative_path = full_path.name

    return str(relative_path).replace("\\", "/")
