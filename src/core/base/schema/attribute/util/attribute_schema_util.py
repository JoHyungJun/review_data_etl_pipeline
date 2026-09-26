"""
attribute_schema_util.py
------------------------

attribute schema 관련 util 모듈
"""


import copy
import logging
from typing import TypeVar, Type, Any, cast, Optional

import pandas as pd

from core.base.schema.attribute.base_attribute_schema import BaseAttributeSchema
from core.base.type.generic_types import TBaseAttributeSchema
from util.column_util import build_indexed_column_name, rename_safely
from util.logging_util import logging_error_event


# build_attribute_mapping() 메서드에서 활용하기 위한 제네릭 타입
TSourceSchema = TypeVar("TSourceSchema", bound=BaseAttributeSchema)
TTargetSchema = TypeVar("TTargetSchema", bound=BaseAttributeSchema)


def build_attribute_mapping(
        source_schema: Type[TSourceSchema],
        target_schema: Type[TTargetSchema],
        indexed_mapping_delimiter: str = '',
) -> tuple[dict[str, str], Type[TSourceSchema]]:
    """
    두 BaseAttributeSchema 파라미터에 대하여
    rename 에 필요한 매핑 dict, 매핑 결과 값이 상수에 반영된 매핑 schema 를 tuple 로 반환

    매핑 dict 설정 규칙은 다음과 같음
    1. source_schema 내부에 선언된 상수들을 순회
    2. 개별 상수에 대하여, 같은 이름 (attr_name) 으로 선언된 상수가 target_schema 에 존재한다면
       {source_schema.상수명: target_schema.상수명} 매핑 정보를 dict 에 추가
    3. 개별 상수에 대하여, 같은 이름 (attr_name) 으로 선언된 상수가 target_schema 에
       존재한다면 target_schema 의 상수 값 (target_value) 을 mapping schema 에 반영
       존재하지 않는다면 source_schema 의 기존 상수 값 (source_value) 을 mapping schema 에 반영

    해당 메서드로 반환되는 dict 는 pandas.DataFrame.rename() 사용 목적으로 활용되며,
    rename 이후 컬럼명은 반환되는 mapping schema 의 상수 값이 됨

    주의 사항
    - return 되는 schema 는 두 schema 전부를 합쳐서 반환하는 것이 아닌,
      source schema 를 기준으로 같은 상수 (변수명) 가 target schema 에 있다면 그 상수 값을 덮어쓰는 것 뿐임
    - return 되는 반환 값은 각각 다음과 같은 특징을 가짐
        - dict[str, str]:
            rename 을 위한 mapping dict 이며,
            INDEXED_COLUMNS_NESTED_FORMAT 이 가진 nested 구조 역시 flatten 하게 일대일 대응 dict 으로 반환
        - Type[TSourceSchema]:
            컬럼명 상수 사용을 위한 BaseAttributeSchema 자식 클래스이며,
            INDEXED_COLUMNS_NESTED_FORMAT 상수는 nested 구조의 dict 으로 반환

    :param source_schema: 매핑 대상 상수 스키마 클래스 BaseAttributeSchema(TSourceSchema)
    :param target_schema: 매핑 기준 상수 스키마 클래스 BaseAttributeSchema(TTargetSchema)
    :param indexed_mapping_delimiter: INDEXED_COLUMNS_NESTED_FORMAT flatten 매핑에 쓰일 구분자 str
    :return: tuple[상수 매핑 정보 dict, 상수 매핑 반영 BaseAttributeSchema(TSourceSchema)]
    """

    schema_mapping: dict[str, Any] = {}
    column_mapping: dict[str, str] = {}

    missing_value = []

    # flatten 컬럼명 매핑
    source_constants_mapping = source_schema.get_constants_name_value_mapping()
    target_constants_mapping = target_schema.get_constants_name_value_mapping()

    mapping_schema_indexed_columns_mapping = copy.deepcopy(source_schema.INDEXED_COLUMNS_NESTED_FORMAT or {})
    target_schema_indexed_columns_mapping = copy.deepcopy(target_schema.INDEXED_COLUMNS_NESTED_FORMAT or {})

    # 새로운 클래스에 매핑될 상수 초기화
    for source_key, source_value in source_constants_mapping.items():

        if source_key in target_constants_mapping.keys():

            target_value = target_constants_mapping.get(source_key)

            # schema 매핑
            # 일반 상수의 경우 단순 덮어쓰기 (None 값의 상수도 스키마 자체엔 넣음)
            schema_mapping[source_key] = target_value

            if source_value is not None and isinstance(source_value, str):
                if (
                        source_value in mapping_schema_indexed_columns_mapping
                        and target_value in target_schema_indexed_columns_mapping
                ):
                    # 같은 상수명이라면 indexed mapping key 명 (상수값) 도 target 기준으로 수정
                    # source key 제거
                    mapping_schema_indexed_columns_mapping.pop(source_value)

                    # target key (== target value) 재삽입
                    mapping_schema_indexed_columns_mapping[target_value] \
                        = target_schema_indexed_columns_mapping[target_value]

                # column 매핑
                # rename 을 위한 INDEXED_COLUMNS_NESTED_FORMAT 의 flatten 매핑
                indexed_mapping = build_flatten_indexed_columns_mapping(
                    source_schema=source_schema,
                    target_schema=target_schema,
                    constant_name=source_key,
                    delimiter=indexed_mapping_delimiter,
                )

                # indexed mapping 이 존재하지 않을 경우 단순 상수 매핑
                if not indexed_mapping:
                    column_mapping[source_value] = target_constants_mapping[source_key]
                else:
                    column_mapping.update(indexed_mapping)

        # target 엔 없고 source 에만 존재하는 상수는 로그 처리
        else:
            schema_mapping[source_key] = source_value
            missing_value.append(source_key)

    if missing_value:
        logging.warning(f"[SKIP] source_schema={source_schema.__name__}, target_schema={target_schema.__name__}, "
                        f"missing_values={missing_value}: Some values are not defined in target schema")

    # 매핑 결과가 반영된 schema
    mapped_schema = cast(
        Type[TSourceSchema],
        type(
            f"Mapping{source_schema.__name__}To{target_schema.__name__}",
            (BaseAttributeSchema,),
            schema_mapping,
        ),
    )

    # 덮어쓰기
    mapped_schema.INDEXED_COLUMNS_NESTED_FORMAT = dict(mapping_schema_indexed_columns_mapping)

    return column_mapping, mapped_schema


def build_flatten_indexed_columns_mapping(
        source_schema: Type[BaseAttributeSchema],
        target_schema: Type[BaseAttributeSchema],
        constant_name: str,
        delimiter: str = '',
) -> dict[str, str]:
    """
    두 BaseAttributeSchema 간 INDEXED_COLUMNS_NESTED_FORMAT 을 flatten 매핑 후 반환

    해당 메서드는 INDEXED_COLUMNS_NESTED_FORMAT 에 대해서만 특정 규칙에 따라 매핑을 수행하며,
    개별 상수 매핑에는 관여하지 않음

    매핑 규칙
    - rename 용 매핑 dict 반환에 목적이 있기 때문에,
      매핑 방향성은 항상 source to target

    - 대상 두 schema 가 최소 검증 규칙 (해당 constant name 으로 선언된 상수가 없음) 이 지켜지지 않거나,
      INDEXED_COLUMNS_NESTED_FORMAT 가 모두 None 일 경우
      : {} 반환

    - 한 쪽의 INDEXED_COLUMNS_NESTED_FORMAT 에는 key 가 존재하나,
      다른 쪽의 INDEXED_COLUMNS_NESTED_FORMAT 는 None 이거나 key 가 존재하지 않을 경우
      : key 가 존재하는 쪽의 첫 번째 index, 존재하지 않는 쪽의 상수 매핑
        (ex. {REVIEW_ID_1: REVIEW_ID})

    - 두 schema 의 INDEXED_COLUMNS_NESTED_FORMAT 모두에 key 가 존재할 땐,
      길이가 짧은 쪽을 기준으로 동일 index 로 매핑

    :param source_schema: 매핑 대상 BaseAttributeSchema
    :param target_schema: 매핑 기준 BaseAttributeSchema
    :param constant_name: 매핑 대상 상수명 str
    :param delimiter: index 구분자 str
    :return: INDEXED_COLUMNS_NESTED_FORMAT 컬럼에 대한 flatten mapping dict[str, str]
    """

    warning_msgs = []

    # 최소 요건 검증 (양쪽의 key 가 schema 에 있어야 함)
    source_constants = source_schema.get_constants_name_value_mapping()
    if not (constant_name in source_constants.keys()):
        warning_msgs.append(
            f"[VALIDATE] target_schema={source_schema.__name__}, target_key={constant_name}: "
            f"Not found constant in schema - invalid validation"
        )

    target_constants = target_schema.get_constants_name_value_mapping()
    if not (constant_name in target_constants.keys()):
        warning_msgs.append(
            f"[VALIDATE] target_schema={target_constants.__name__}, target_key={constant_name}: "
            f"Not found constant in schema - invalid validation"
        )

    if warning_msgs:
        for msg in warning_msgs:
            logging.warning(msg)

        return {}

    source_indexed_mapping = source_schema.INDEXED_COLUMNS_NESTED_FORMAT
    target_indexed_mapping = target_schema.INDEXED_COLUMNS_NESTED_FORMAT

    # 검증 최소 요건 (양측 동시에 INDEXED_COLUMNS_NESTED_FORMAT 가 존재) 확인
    if source_indexed_mapping is None and target_indexed_mapping is None:
        return {}

    source_indexed_key = source_constants.get(constant_name)
    target_indexed_key = target_constants.get(constant_name)

    # 해당 상수 값의 None 여부 검증
    if source_indexed_key is None or target_indexed_key is None:
        return {}

    # 해당 상수 값의 str 여부 검증
    if not isinstance(source_indexed_key, str) or not isinstance(target_indexed_key, str):
        return {}

    # validate
    # target_indexed None or X
    if target_indexed_mapping is None or target_indexed_mapping.get(target_indexed_key) is None:

        # source_indexed None or X / target_indexed None or X
        if source_indexed_mapping is None or source_indexed_mapping.get(source_indexed_key) is None:
            return {}

        # source_indexed O / target_indexed None or X
        source_value = source_indexed_mapping.get(source_indexed_key)
        if not isinstance(source_value, list):
            logging.warning(
                f"[FORMAT] target_value={source_schema.__name__}.INDEXED_COLUMNS_NESTED_FORMAT.{constant_name}: "
                f"Invalid non-list value"
            )
            return {}

        logging.debug(
            f"[FORMAT] source_schema={source_schema.__name__}, target_schema={target_schema.__name__}, "
            f"constant_name={constant_name}: "
            f"Only source schema's indexed mapping has key - "
            f"mapped '1-suffixed source constant value' to 'target constant value'"
        )
        return {
            build_indexed_column_name(source_value[0], 1, delimiter):
                target_constants.get(constant_name)
        }

    # target O
    target_value = target_indexed_mapping.get(target_indexed_key)

    # source None or X / target O
    if source_indexed_mapping is None or source_indexed_mapping.get(source_indexed_key) is None:
        if not isinstance(target_value, list):
            logging.warning(
                f"[FORMAT] target_value={target_schema.__name__}.INDEXED_COLUMNS_NESTED_FORMAT.{constant_name}: "
                f"Invalid non-list value"
            )
            return {}

        logging.debug(
            f"[FORMAT] source_schema={source_schema.__name__}, target_schema={target_schema.__name__}, "
            f"constant_name={constant_name}: "
            f"Only target schema's indexed mapping has key - "
            f"mapped 'source constant value' to '1-suffixed target constant value'"
        )
        return {
            source_constants.get(constant_name):
                build_indexed_column_name(target_value[0], 1, delimiter)
        }

    # source O / target O
    source_value = source_indexed_mapping.get(source_indexed_key)

    # type 검증
    if type(source_value) != type(target_value):
        logging_error_event(
            log_message="Type mismatch",
            log_metadata={
                "source_type": type(source_value),
                "target_type": type(target_value),
            },
            log_prefix="FORMAT"
        )
        raise ValueError(
            f"스키마 INDEXED_COLUMNS_NESTED_FORMAT 병합에서 타입이 다른 두 변수를 병합할 수 없습니다. "
            f"{source_schema.__name__}, {target_schema.__name__} 의 {constant_name} 상수 코드를 확인해주세요."
        )

    # index length 검증 (위의 분기에 따라 source_value 가 list 라면 target_value 또한 list)
    elif isinstance(source_value, list):

        length = len(source_value)

        if len(source_value) != len(target_value):
            logging.warning(
                f"[FORMAT] source_schema={source_schema.__name__}, target_schema={target_schema.__name__}, "
                f"source_value_len={len(source_value)}, target_value_len={len(target_value)}: "
                f"Length mismatch - mapping with min length indexing"
            )

            length = min(len(source_value), len(target_value))

        return {
            build_indexed_column_name(source_value[idx], idx + 1, delimiter):
                build_indexed_column_name(target_value[idx], idx + 1, delimiter)
            for idx in range(0, length)
        }

    else:
        return {}


def build_prefixed_df_and_attribute_schema(
        df: pd.DataFrame,
        source_schema: Type[TBaseAttributeSchema],
        full_prefix: str,
) -> tuple[pd.DataFrame, Type[TBaseAttributeSchema]]:
    """
    파라미터의 source attribute schema 기준으로,
    모든 상수 값에 prefix 가 적용된 새로운 attribute schema 와
    모든 컬럼명을 prefix 가 붙은 컬럼명으로 rename 하는 df 반환

    생성 규칙
    - 기존 schema 가 가지고 있는 모든 상수 보유 및 상수명 유지
    - 개별 상수 값에 기존 같은 "prefix + 상수 값" 의 값으로 초기화
      (dict 의 경우 key 에도 prefix 적용)
    - str 외의 다른 데이터 타입 (ex. list, dict) 의 경우 재귀적으로 개별 원소에 수행하며,
      만약 재귀 마지막 단계의 값이 str 이 아닐 경우 기존 값을 그대로 상속
    - 파라미터의 df 또한 반환되는 prefixed attribute schema 와 일치하는 컬럼명으로 rename

    :param df: 컬럼명 prefix 대상 pandas.DataFrame
    :param source_schema: prefix 대상 Type[TAttributeSchema]
    :param full_prefix: delimiter 를 포함한 전체 prefix str
    :return: prefix 처리가 끝난 tuple[pandas.DataFrame, Type[TAttributeSchema]]
    """

    prefixed_attribute_schema = build_prefixed_attribute_schema(
        source_schema=source_schema,
        full_prefix=full_prefix,
    )

    mapping_dict, mapping_schema = build_attribute_mapping(
        source_schema=source_schema,
        target_schema=prefixed_attribute_schema,
    )

    prefixed_df = rename_safely(df=df, column_name_mapping=mapping_dict)

    return prefixed_df, prefixed_attribute_schema


def build_prefixed_attribute_schema(
        source_schema: Type[TBaseAttributeSchema],
        full_prefix: str,
) -> Type[TBaseAttributeSchema]:
    """
    source schema 에 선언된 상수 기반, 모든 상수 값에 prefix 가 적용된 새로운 attribute schema 반환

    생성 규칙
    - 기존 schema 가 가지고 있는 모든 상수 보유 및 상수명 유지
    - 개별 상수 값에 기존 같은 "prefix + 상수 값" 의 값으로 초기화
      (dict 의 경우 key 에도 prefix 적용)
    - str 외의 다른 데이터 타입 (ex. list, dict) 의 경우 재귀적으로 개별 원소에 수행하며,
      만약 재귀 마지막 단계의 값이 str 이 아닐 경우 기존 값을 그대로 상속

    :param source_schema: prefix 대상 Type[TAttributeSchema]
    :param full_prefix: delimiter 를 포함한 전체 prefix str
    :return: prefix 처리가 끝난 Type[TAttributeSchema]
    """

    # suffix 가 적용된 새로운 mapping
    prefixed_constants_mapping = {
        constant_name: apply_prefix_recursively(prefix=full_prefix, value=constant_value)
        for constant_name, constant_value in source_schema.get_constants_name_value_mapping().items()
    }

    return cast(
        Type[TBaseAttributeSchema],
        type(
            f"Prefixed{source_schema.__name__}",
            (BaseAttributeSchema,),
            prefixed_constants_mapping,
        )
    )


def apply_prefix_recursively(
        prefix: str,
        value: Any,
) -> Any:
    """
    str, dict, list 타입의 value 에 재귀적으로 prefix 를 붙이고 반환

    :param prefix: delimiter 를 포함한 전체 prefix str
    :param value: prefix 대상 값 Any
    :return: prefix 처리가 끝난 값 Any
    """

    if value is None:
        return None
    elif isinstance(value, str):
        return build_prefixed_value(prefix=prefix, value=value)
    elif isinstance(value, dict):
        return {
            apply_prefix_recursively(prefix=prefix, value=k):
                apply_prefix_recursively(prefix=prefix, value=v)
            for k, v in value.items()
        }
    elif isinstance(value, list):
        return [apply_prefix_recursively(prefix=prefix, value=v) for v in value]
    else:
        return value


def build_prefixed_value(
        prefix: str = "",
        delimiter: str = "",
        value: str = "",
) -> str:
    """
    prefix 와 delimiter 를 적용한 value 반환

    파라미터를 자유롭게 선택하여 활용 가능

    :param prefix: 적용 대상 prefix str
    :param delimiter: 적용 대상 구분자 str
    :param value: 적용 대상 값 str
    :return: prefix + delimiter + value str
    """

    return f"{prefix}{delimiter}{value}"


def build_contains_flatten_mapping_by_priority(
        prioritized_attribute_schemas: list[Type[BaseAttributeSchema]],
        target_schema: Type[BaseAttributeSchema]
) -> dict[str, str]:
    """
    target schema 에 선언된 상수 기반,
    우선 순위 (prioritized_attribute_schemas 선언 순서) 에 따라 같은 상수명을 가진 상수값을 초기화 하고,
    초기화 되지 않은 상수는 기존 값으로 초기화 한 새로운 attribute schema 반환

    contains 규칙
    - prioritized_attribute_schemas 의 순서대로 초기화

    - 빠른 순서의 상수 값으로 초기화, 이후 동일한 상수는 값을 덮어쓰지 않음

    - flatten mapping 을 기준으로 로직 수행

    - prioritized_attribute_schemas 의 attribute schema 에 존재하지 않으면서,
      target attribute schema 에만 존재하는 상수는
      기존 target attribute schema 가 가지고 있던 값으로 초기화

    :param prioritized_attribute_schemas: 우선 순위 순으로 선언된 attribute schema list[Type[BaseAttributeSchema]]
    :param target_schema: 기준이 되는 Type[BaseAttributeSchema]
    :return: flatten 된 {상수명: 상수값} 일대일 매핑 정보 dict[str, str]
    """

    # target schema 기반, 선언된 flatten 상수 전체 추출 후 None 초기화
    target_constants_flatten_mapping = target_schema.get_flatten_constants_name_value_mapping()

    contains_constants_flatten_mapping: dict[str, Optional[str]] = {
        k: None
        for k in target_constants_flatten_mapping.keys()
    }

    # 파라미터로 전달된 우선 순위에 따라 None 이 아닌 상수만 초기화 (외부 schema)
    for attribute_schema in prioritized_attribute_schemas:
        if attribute_schema is None:
            continue

        current_constants_mapping = attribute_schema.get_flatten_constants_name_value_mapping()

        for constant_name, constant_value in current_constants_mapping.items():
            if constant_name not in contains_constants_flatten_mapping.keys():
                continue

            # priority 에 따라 초기화 되지 않은 상수만 덮어쓰기
            if contains_constants_flatten_mapping[constant_name] is None:
                contains_constants_flatten_mapping[constant_name] = constant_value

    # 초기화 되지 않은 상수의 경우 기존 target schema 의 기존 값으로 초기화 (fallback)
    for constant_name, constant_value in target_constants_flatten_mapping.items():
        if contains_constants_flatten_mapping[constant_name] is None:
            contains_constants_flatten_mapping[constant_name] = constant_value

    return contains_constants_flatten_mapping


def validate_column_name(column_name: Optional[str]) -> Optional[str]:
    """
    파라미터로 들어온 column name 검증

    검증 규칙
    - None, ' ', '' 문자열은 invalid 값으로 취급
    - invalid 값의 경우 None 반환
    - valid 값의 경우 .strip() 적용한 값이 반환

    :param column_name: 검증 대상 column name str
    :return: 파라미터로 전달된 column_name 에 .strip() 적용된 str
    """

    if column_name is None:
        return None

    column_name = column_name.strip()

    if not column_name:
        return None

    return column_name


def build_rename_mapping_by_constants_flatten_mapping(
        source_constants_flatten_mapping: dict[str, str],
        target_constants_flatten_mapping: dict[str, str],
) -> dict[str, str]:
    """
    서로 다른 schema 의 두 flatten mapping (get_flatten_constants_name_value_mapping()) 에서
    같은 key 에 해당하는 value 끼리의 mapping 반환

    해당 메서드는 두 flatten mapping 으로부터 rename 용 mapping dict 를 추출하기 위해 활용

    :param source_constants_flatten_mapping: 매핑 대상 schema 의 flatten 매핑 dict[str, str]
    :param target_constants_flatten_mapping: 매핑 기준 schema 의 flatten 매핑 dict[str, str]
    :return: rename 용 컬럼명 flatten 매핑 dict[str, str]
    """

    rename_mapping: dict[str, str] = {}

    for source_key, source_column in source_constants_flatten_mapping.items():

        target_column = target_constants_flatten_mapping.get(source_key)

        # None 값 skip
        if source_column is None or target_column is None:
            continue

        rename_mapping[source_column] = target_column

    return rename_mapping
