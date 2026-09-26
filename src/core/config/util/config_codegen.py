"""
config_codegen.py
-----------------

스키마 dict 를 기반으로 Section 및 Option 명 상수 모듈 자동 생성하는 유틸리티 모듈

스키마 정보를 담은 dict 를 기반하여,
Section 명을 클래스명, Option 명을 하위 상수명 및 상수값으로 갖는 상수 클래스 모듈 schema_constants.py 를 자동 작성함

자동 생성된 상수 모듈은 코드 내에서 스키마 및 설정값 (ConfigRegistry) 에 접근 시 하드코딩 및 오탈자를 방지하고자 활용되며,
따라서 스키마 변경 시 해당 코드 실행을 권고
"""


import inspect
import re
from pathlib import Path
from typing import Union

from core.config.model.config_base_section_option import Section, Option
from core.config.model.config_schema import get_default_schema
from util.logging_util import logging_file_event
from util.path_util import get_or_create_directory, get_relative_path


def generate_constants_from_schema(schema: dict[str, Section], constants_output_path: Union[str, Path]) -> None:
    """
    스키마 dict 를 기반으로 Section 및 Option 명 상수 모듈 자동 생성

    :param schema: schema dict[str, Section]
    :param constants_output_path: 상수 모듈 output save 경로 Union[str, Path]
    :return: 없음
    """

    # 모듈 최상단 docstring 부
    lines = [
        '"""',
        f"{constants_output_path.name}",
        f"{'-' * len(constants_output_path.name)}",
        "",
        "스키마 및 설정값 정의에 사용되는 Section, Option 이름에 대한 상수 모음 모듈",
        "",
        "클래스명 및 해당 클래스의 하위 상수 SECTION_KEY 은 Section 명을 의미하며,",
        "하위 상수명 및 상수값은 Option 의 key 명을 의미함",
        "",
        "주의 사항",
        f"- 해당 모듈은 {inspect.currentframe().f_code.co_name}() 메서드를 통해 자동 생성되며,",
        f"  실제 스키마의 작성 기준 (truth of source) 은 {get_relative_path(get_default_schema)} 모듈이고,",
        "  상수 모듈 작성 과정에서 정보가 변경될 수 있음을 주의",
        "",
        "- 상수들은 코드 내에서 스키마 및 설정값 접근 시 하드코딩 및 오탈자 방지를 위해 활용되므로,",
        "  해당 모듈의 직접 수정을 금지,",
        "  스키마 변경 시에는 반드시 truth of source 수정 후 codegen 메서드 실행으로",
        "  데이터간의 정합성을 맞추는 방법을 강력히 강제",
        "",
        "- 외부 파일로 작성되는 설정값들은,",
        "  반드시 이 상수 모듈에 정의된 key 명으로 Section/Option 명이 정의되어야 함",
        '"""',
        "",
        ""
    ]

    for section_key, section_obj in schema.items():
        # 클래스명에서 특수문자 제외
        class_name = re.sub(r'[^a-zA-Z0-9_]', '', section_key.upper())
        lines.append(f"class {class_name}:")

        # 최상단 SECTION_KEY 추가
        lines.append(f"    SECTION_KEY = '{section_key}'\n")

        options: dict[str, Option] = section_obj.options

        # 해당 Section 에 Option 이 존재한다면 개별 Option 에 대한 상수 변수 추가
        if options:
            for option_key in options.keys():
                const_name = re.sub(r'[^a-zA-Z0-9_]', '', option_key.upper())
                lines.append(f"    {const_name} = '{option_key}'")

        else:
            lines.append("    pass")

        lines.append("\n")

    # YAML 파일로 출력
    get_or_create_directory(full_path=constants_output_path.parent)
    constants_output_path.write_text("\n".join(lines), encoding="utf-8")

    logging_file_event(
        file_path=constants_output_path,
        log_prefix="SAVE",
        log_metadata={
            "process": "generate_constants_from_yaml"
        },
        log_level="debug",
    )
