"""
config_util.py
--------------

애플리케이션 기본 설정값 스키마 (yaml) setup 관련 util 모듈
"""


import logging
from collections import OrderedDict
from datetime import datetime, date, time
from enum import Enum
from pathlib import Path
from typing import Optional, Union, Any

import yaml

from core.config.model.config_base_section_option import Section, Option, OptionMeta
from core.config.model.config_schema import get_default_schema
from util.logging_util import logging_error_event, logging_file_event
from copy import deepcopy

from util.path_util import get_relative_path


# Section-based configuration 구조의 싱글톤 스키마 전역 변수
_singleton_config_schema: Optional[dict[str, Section]] = None


def load_yaml_config_to_dict(yaml_path: Union[Path, str]) -> dict:
    """
    YAML 파일 load 및 파싱 후 dict 형태로 반환
    
    해당 메서드는 YAML config schema dict 생성에도 사용되므로
    엄격한 분기 처리 (예외 시 None 반환 없이 무조건 에러 반환)

    :param yaml_path: YAML 파일 경로
    :return: load 및 파싱된 YAML 데이터 dict
    """

    try:
        with open(Path(yaml_path), encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError as e:
        logging_error_event(
            log_prefix="LOAD",
            log_metadata={
                "file_path": yaml_path,
            },
            log_message="Not found YAML configuration file",
            log_message_detail=str(e),
        )
        raise e
    except yaml.YAMLError as e:
        logging_error_event(
            log_prefix="PARSE",
            log_metadata={
                "file_path": yaml_path,
            },
            log_message="Parsing error detected in the YAML file",
            log_message_detail=str(e),
        )
        raise RuntimeError(f"YAML 파일에서 구문 오류를 발견했습니다.:\n{e}")
    except Exception as e:
        logging_error_event(
            log_prefix="LOAD",
            log_metadata={
                "file_path": yaml_path,
            },
            log_message="While loading YAML file",
            log_message_detail=str(e),
        )
        raise e


def to_serializable(obj: Any) -> Optional[Any]:
    """
    파라미터의 값을 자료형에 따라 분기하여 직렬화 후 반환

    해당 직렬화 로직은 YAML 포맷의 파싱을 기준으로 함

    :param obj: 직렬화 대상 객체
    :return: 직렬화 가능한 형태 데이터 Optional[Any]
    """
    
    if obj is None:
        return None

    # Enum 의 경우 내부 상수를 파싱
    if isinstance(obj, Enum):
        return str(obj.value)

    if isinstance(obj, (str, int, float, bool)):
        return obj

    # 날짜, 시간의 경우 포맷에 따른 파싱
    if isinstance(obj, (datetime, date, time)):
        return obj.isoformat()

    if isinstance(obj, Path):
        return str(obj)

    if isinstance(obj, (list, set, tuple)):
        return [to_serializable(v) for v in obj]

    if isinstance(obj, (dict, OrderedDict)):
        return {str(k): to_serializable(v) for k, v in obj.items()}

    if hasattr(obj, "__dict__"):
        return {str(k): to_serializable(v) for k, v in vars(obj).items()}

    return str(obj)


def dump_schema_to_yaml(
        schema_dict: dict,
        yaml_output_path: Union[str, Path],
) -> dict:
    """
    스키마 dict 를 YAML 포맷으로 파싱하여 save

    :param schema_dict: 스키마 dict
    :param yaml_output_path: 출력 YAML 경로
    :return: 직렬화된 dict
    """

    warning_comment = (
        f"# [WARN] \n"
        f"# 이 파일은 source of truth 결과물의 단순 출력물이며 명세를 위해 작성된 파일입니다.\n"
        f"# 해당 파일의 값을 직접 수정해도 애플리케이션에 반영되지 않습니다.\n"
        f"# 스키마 변경을 원하시면 {get_relative_path(get_default_schema)} 를 수정하십시오.\n\n\n\n"
    )

    data = to_serializable(schema_dict)

    try:

        with open(Path(yaml_output_path), "w", encoding="utf-8") as file:
            file.write(warning_comment)

            yaml.safe_dump(
                data,
                file,
                sort_keys=False,
                allow_unicode=True,
                default_flow_style=False,
                indent=2,
                width=80,
                line_break='\n\n'
            )
    except FileNotFoundError:
        logging_file_event(
            file_path=yaml_output_path,
            log_prefix="SAVE",
            log_metadata={
                "process": "dump_schema_to_yaml"
            },
            log_level="warning",
            log_message="While dumping schema dict to yaml",
        )
    except Exception as e:
        logging_error_event(
            exception_instance=e,
            log_message="While writing yaml for dump schema",
            log_message_detail=str(e),
            log_metadata={
                "process": "dump_schema_to_yaml"
            },
        )
        raise

    return data


def parse_yaml_dict_to_schema_format(yaml_dict: dict) -> dict[str, Section]:
    """
    YAML dict 데이터를 Section-based configuration (Section/Option/OptionMeta) 구조 dict 로 변환 및 반환

    :param yaml_dict: YAML dict
    :return: 파싱된 Section-based configuration 구조의 dict
    """

    if not isinstance(yaml_dict, (dict, OrderedDict)):
        raise TypeError("파싱 대상이 Dict 형태가 아닙니다. 파라미터를 확인해주세요.")

    schema = {}

    # Section 및 Option 파싱 로직
    for section_name, section_dict in yaml_dict.items():
        section = Section(section_name)

        options_dict = section_dict.get("options", {})
        for option_key, option_value in options_dict.items():
            value = option_value.get("value")
            meta_data = option_value.get("meta", {})

            meta = OptionMeta.from_dict(meta_data)
            option = Option(key=option_key, value=value, meta=meta)

            section.add_option(option)

        schema[section_name] = section

    return schema


def merge_schema_with_config(
        section_based_schema_dict: dict[str, Section],
        section_based_config_dict: dict[str, Section],
) -> dict[str, Section]:
    """
    스키마 관리 dict 와 section based 로 파싱된 config dict 두 정보를 병합

    파라미터로 들어오는 두 dict 는 반드시 Section-based 포맷이어야 하며,
    dict[str, Section] 구조 및 Section 객체 내부에 Option 객체들이 존재하는 구조여야 함

    :param section_based_schema_dict: Section-based configuration 구조의 schema dict[str, Section]
    :param section_based_config_dict: 외부 설정 파일 기반 Section-based configuration 구조의 config dict[str, Section]
    :return: 병합된 Section-based configuration 구조의 dict[str, Section]
    """

    # 안전성을 위해 싱글톤 객체 정보를 deep copy
    merged_schema_dict = deepcopy(section_based_schema_dict)

    for config_section_key, config_section_obj in section_based_config_dict.items():

        # 스키마에 존재하지 않는 section 정보는 추가
        if config_section_key not in merged_schema_dict:
            logging.info(f"[MERGE] process=merge_schema_with_config, target_section={config_section_key}: "
                         f"Found new section from config not in schema")

            merged_schema_dict[config_section_key] = Section(config_section_key)
            continue

        # Section 객체인지 검증 후 options dict 가져오기
        options = getattr(config_section_obj, "options", None)
        if options is None:
            logging.warning(
                f"[SKIP] process=merge_schema_with_config, target_section={config_section_key}: "
                f"Found invalid section object while merging schema - section object has no 'options' attribute"
            )
            continue

        schema_section_obj = merged_schema_dict[config_section_key]

        for option_key, option_obj in options.items():

            # 같은 key 데이터에 대해선 외부 설정값을 우선 순위로 두어 값을 오버라이딩
            if option_key in schema_section_obj.options:
                old_value = schema_section_obj.options[option_key].value
                schema_section_obj.options[option_key].set_value(option_obj.value)

                logging.debug(
                    f"[UPDATE] process=merge_schema_with_config, target_key={config_section_key}.{option_key}, "
                    f"target_value={old_value}, updated_value={option_obj.value}"
                )

            # 스키마에 정의되지 않은 외부 설정값은 추가
            else:
                schema_section_obj.add_option(deepcopy(option_obj))

                logging.info(f"[MERGE] process=merge_schema_with_config, "
                             f"target_key={config_section_key}.{option_key}, target_value={option_obj}: "
                             f"Found new option from config not in schema")

    return merged_schema_dict


def setup_yaml(output_yaml_path: Union[Path, str]) -> None:
    """
    코드에 정의된 스키마 정보를 load 후 YAML 파일에 삽입하여 초기화

    :param output_yaml_path: YAML 산출물 save 경로
    :return: 없음
    """

    default_schema = get_default_schema()
    dump_schema_to_yaml(default_schema, Path(output_yaml_path))


def initialize_singleton_schema() -> None:
    """
    싱글톤으로 관리되는 스키마 dict 초기화

    애플리케이션 최초 실행 setup 시 한 번만 실행을 권고

    :return: 없음
    """

    global _singleton_config_schema

    if _singleton_config_schema is None:
        _singleton_config_schema = get_default_schema()


def get_singleton_schema() -> dict[str, Section]:
    """
    정의된 싱글톤 스키마 dict 를 반환

    :return: 싱글톤 스키마 dict[str, Section]
    """

    global _singleton_config_schema

    if _singleton_config_schema is None:
        _singleton_config_schema = get_default_schema()

    return _singleton_config_schema
