"""
path_constants.py
-----------------

프로젝트의 구조 통일, 산출물 생성/접근/저장 관리, 파이프라인 실행의 편의성 등을 위한
주요 디렉토리/파일/모듈 경로에 대한 상수 모음 모듈
(로컬 용)

프로젝트 핵심 디렉토리 ('src', 'datas', 'sentiment_model', 'logs') 기준 상위 디렉토리를 프로젝트 최상위 디렉토리라 판단하고
최상위 디렉토리를 기준, 주요 디렉토리의 경로를 계산

다음과 같은 환경에선 경로 탐색이 실패할 수 있음
- 단일 모듈의 독립 실행
- 기본 구조와 다른 디렉토리 구조 환경 실행
- 서버/클라우드 환경 등 로컬 외 환경 실행

핵심 로직 (entrypoints 하위 모듈) 은 메서드 파라미터 및 config 객체 init 파라미터를 통해
입출력 경로를 수정할 수 있도록 확장성 있게 설계되었으므로
불완전한 프로젝트 혹은 다른 환경 실행에서는 코드 수정을 통한 직접 경로를 조정을 권고
(파라미터의 default 값은 현재 모듈의 상수들을 사용)
"""


from pathlib import Path

from config.constant.name_constants import *


# ------------------------------------------
# 루트 (최상위 디렉토리) 경로 탐색
# ------------------------------------------

def get_base_directory() -> Path:
    """
    프로젝트 최상위 디렉토리를 탐색하여 반환

    프로젝트 핵심 디렉토리 ('src') 가 존재하는 상위 디렉토리를 최상위 디렉토리라 판단함

    주의 사항
    - 판단 기준은 핵심 디렉토리인 'src' 이지만, 환경별 필수 디렉토리는 추가적으로 존재하므로,
      개별 bootstrap 혹은 최초 실행 과정에서 환경별 필수 디렉토리가 존재하는지에 대한 검증 과정을 반드시 거쳐야 함

    :return: 프로젝트의 최상위 디렉토리 pathlib.Path
    """

    current_path = Path(__file__).resolve()

    for parent_path in (current_path, *current_path.parents):
        if (parent_path / SRC_DIRECTORY_NAME).is_dir():
            return parent_path

    raise RuntimeError("최상위 폴더를 찾을 수 없습니다. 프로젝트 구조를 다시 확인해주세요.")


# root 디렉토리
BASE_DIRECTORY_PATH = get_base_directory()

# 주요 (상위) 디렉토리
SRC_DIRECTORY_PATH = BASE_DIRECTORY_PATH / SRC_DIRECTORY_NAME
DATAS_DIRECTORY_PATH = BASE_DIRECTORY_PATH / DATAS_DIRECTORY_NAME
SENTIMENT_MODEL_DIRECTORY_PATH = BASE_DIRECTORY_PATH / SENTIMENT_MODEL_DIRECTORY_NAME
LOGS_DIRECTORY_PATH = BASE_DIRECTORY_PATH / LOGS_DIRECTORY_NAME
CONFIG_DIRECTORY_PATH = BASE_DIRECTORY_PATH / CONFIG_DIRECTORY_NAME

SRC_CONFIG_DIRECTORY_PATH = SRC_DIRECTORY_PATH / SRC_CONFIG_DIRECTORY_NAME


# sentiment 관련 디렉토리
# 추론 모델이 위치하는 디렉토리
TRAINED_SENTIMENT_MODEL_DIRECTORY_PATH = (
        SENTIMENT_MODEL_DIRECTORY_PATH
        / 'roberta-finetuned'
        / 'content'
        / 'drive'
        / 'MyDrive'
        / 'roberta-finetuned'
)

# 관련 로그가 위치하는 디렉토리
SENTIMENT_LOGS_DIRECTORY = LOGS_DIRECTORY_PATH / SENTIMENT_LOGS_DIRECTORY_NAME


# config 관련 주요 파일, 디렉토리 경로
CONFIG_INI_PATH = CONFIG_DIRECTORY_PATH / CONFIG_INI_FILE_NAME
CONFIG_SCHEMA_YML_PATH = SRC_CONFIG_DIRECTORY_PATH / CONFIG_SCHEMA_YML_FILE_NAME

SCHEMA_CONSTANTS_PY_PATH = SRC_CONFIG_DIRECTORY_PATH / CONFIG_CONSTANTS_DIRECTORY_NAME / SCHEMA_CONSTANTS_PY_FILE_NAME


# 로그 관련 경로
APPLICATION_LOG_PATH = LOGS_DIRECTORY_PATH / APP_LOG_FILE_NAME

SENTIMENT_INFERRED_JSONL_PATH = SENTIMENT_LOGS_DIRECTORY / SENTIMENT_INFERRED_JSONL_FILE_NAME
SENTIMENT_CONFIG_TUNER_STATISTICS_META_JSONL_PATH = (
        SENTIMENT_LOGS_DIRECTORY / SENTIMENT_CONFIG_TUNER_STATISTICS_META_JSONL_FILE_NAME
)
