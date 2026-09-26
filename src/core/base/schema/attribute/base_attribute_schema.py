"""
base_attribute_schema.py
------------------------

해당 프로젝트의 파이프라인 실행 시 중간 결과물의 공통 필수 컬럼을 정의할 상수 추상 클래스들의 부모 클래스 모듈

메타 클래스의 규칙에 따라 반드시 초기화가 필요한 필수 상수에 대해선 NotImplemented 으로 정의해야 하며,
현재 클래스에서 정의된 상수 및 부모 클래스에서 상속 받은 상수들은 반드시 서로 다른 값 (None, NotImplemented 제외) 을 가지고 있어야 함


주의 사항
- 개별 상수가 가지고 있는 값은 매핑될 컬럼명을 의미하며,
  개별 상수명은 반드시 upper case 로, 상수값은 str 로 가져야 함
  (INDEXED_COLUMNS_NESTED_FORMAT 는 예외로 후술)

- NotImplemented 으로 선언된 컬럼의 경우, 반드시 컬럼명을 정의해야 할 Required 컬럼들,
  None 으로 선언된 컬럼의 경우, 반드시 초기화 할 필요는 없는 Optional 컬럼들에 정의

- IMG 와 같이 '{같은 이름의 컬럼명} {index}' 의 구조가 반복되는 경우,
  개별 모든 상수를 정의하지 않고 반복되는 컬럼명만 정의한 후,
  INDEXED_COLUMNS_NESTED_FORMAT dict 에 {상수 : [상수] * 반복 횟수} 의 nested 형태로 선언
  (ex. 이미지_URL 1, 이미지_URL 2 ... 이미지_URL 10
       -> IMG_URL = '이미지_URL', INDEXED_COLUMNS_NESTED_FORMAT = {IMG_URL : [IMG_URL] * 10})

- attribute schema 에 내장된 전체 상수 (컬럼명) 를 활용해야 할 땐
  내장된 get_XXX_mapping() 메서드를 이용하여 정렬 및 인덱스 처리된 전체 컬럼 목록을 활용하길 권고

- 상수들은 기본적으로 컬럼명 순서로 선언해야 함
"""


from typing import Any, Type, cast

from core.base.meta.composite.attribute_schema_meta import AttributeSchemaMeta
from util.column_util import extract_flatten_format_from_nested_format


class BaseAttributeSchema(metaclass=AttributeSchemaMeta):

    INDEXED_COLUMNS_NESTED_FORMAT: dict[str, Any] = None

    @staticmethod
    def _validate_non_target_constant(constant_name: str, constant_value: Any) -> bool:
        # constant name
        # 내부 속성 제외
        if constant_name.startswith("__"):
            return False

        if not constant_name.isupper():
            return False

        # constant value
        # callable (메서드, 클래스) 속성 제외
        if callable(constant_value):
            return False

        return True

    @classmethod
    def get_constants_name_value_mapping(cls) -> dict[str, Any]:
        """
        해당 attribute schema 가 가지고 있는 상수 전체의 매핑 정보를 반환
        
        반환 매핑 값 특징
        - {상수명: 상수값} 일대일 매핑 정보 반환
        - 상수가 선언된 순서 보장
        - None 값을 가진 상수 또한 반환
        
        주의 사항
        - 파싱되지 않은 list, dict 등의 상수값을 그대로 반환하므로,
          rename, reindex 등에 사용하지 않는 것을 권고

        :return: {상수명: 상수값} 일대일 매핑 정보 dict[str, Any]
        """

        constants_name_value_mapping = {}

        for base in reversed(cls.__mro__[:-1]):
            for attr, value in base.__dict__.items():
                # 수집하려는 목표 상수인지 검증
                if not cls._validate_non_target_constant(constant_name=attr, constant_value=value):
                    continue

                # dict 정보일 경우 update
                if isinstance(value, dict):
                    prev_value = constants_name_value_mapping.get(attr, {})

                    if not isinstance(prev_value, dict):
                        prev_value = {}

                    constants_name_value_mapping[attr] = {
                        **prev_value,
                        **value
                    }
                else:
                    constants_name_value_mapping[attr] = value

        return constants_name_value_mapping

    @classmethod
    def get_flatten_constants_name_value_mapping(cls, include_base_constant: bool = False):
        """
        해당 attribute schema 가 가지고 있는 상수 전체의 flatten 매핑 정보 반환

        반환 매핑 값 특징
        - {상수명: 상수값} 일대일 매핑 정보 반환
        - 상수가 선언된 순서 보장 (index 선언 상수의 경우엔 순서가 보장되지 않음)
        - None 값을 가진 상수 또한 반환

        주의 사항
        - 단순 str 이 아닌 list, dict 형태의 상수값을 flatten 처리하여 반환

        - INDEXED_COLUMNS_NESTED_FORMAT 의 flatten 은 스스로의 상수명 ("INDEXED_COLUMNS_NESTED_FORMAT") 을
          prefix key 로 가지지 않음
          (ex. INDEXED_COLUMNS_NESTED_FORMAT = {REVIEW_ID: [REVIEW_ID] * 10} 이라고 가정하면, flatten 시
               INDEXED_COLUMNS_NESTED_FORMAT.REVIEW_ID.1 = REVIEW_ID1 X
               REVIEW_ID.1 = REVIEW_ID1 O)

        - INDEXED_COLUMNS_NESTED_FORMAT 을 제외한 list, dict 값 상수들의 flatten 은 스스로의 상수명을 
          prefix key 로 가짐
          (ex. SOME_CONSTANT = {SOME_KEY: SOME_VALUE} 이라고 가정하면, flatten 시
               SOME_CONSTANT.SOME_KEY = SOME_VALUE)

        - include_base_constant 의 여부에 따라 
          INDEXED_COLUMNS_NESTED_FORMAT 에 key 로 선언된 상수에 대해서
          개별 상수를 매핑 정보에서의 포함, 배제 여부가 결정됨
          (ex. REVIEW_ID = "리뷰 ID", INDEXED_COLUMNS_NESTED_FORMAT = {REVIEW_ID: [REVIEW_ID] * 10} 이라고 가정하면,
               include_base_constant 가 True 일 땐 return {REVIEW_ID, REVIEW_ID.1, REVIEW_ID.2 ...}
               include_base_constant 가 False 일 땐 return {REVIEW_ID.1, REVIEW_ID.2 ...}

        :param include_base_constant: INDEXED_COLUMNS_NESTED_FORMAT 에 포함된 개별 상수를 반환 정보에 포함할지 여부
        :return: flatten 된 {상수명: 상수값} 일대일 매핑 정보 dict[str, str]
        """

        # 상속한 부모 클래스의 상수들까지 모두 수집
        mapped_constants = cls.get_constants_name_value_mapping()
        mapped_schema = cast(
            Type[BaseAttributeSchema],
            type(
                f"MappedBaseAttributeSchema",
                (BaseAttributeSchema,),
                mapped_constants,
            ),
        )

        indexed_mapping = mapped_schema.INDEXED_COLUMNS_NESTED_FORMAT or {}

        flatten_mapping: dict[str, str] = {}
        for constant_name, constant_value in mapped_constants.items():

            # indexed mapping 은 직후 분기에서 일괄 처리
            if constant_value is indexed_mapping:
                continue

            # 단일 상수 (str)
            if isinstance(constant_value, str):
                # indexed 포함 여부에 따라 처리 분기
                if constant_value in indexed_mapping.keys():
                    if include_base_constant:
                        flatten_mapping[constant_name] = constant_value

                    flatten_mapping.update(
                        extract_flatten_format_from_nested_format(
                            nested_format=indexed_mapping.get(constant_value),
                            root_key_prefix=constant_name,
                        )
                    )
                    continue

                flatten_mapping[constant_name] = constant_value
                continue

            # list, dict 상수값을 가진 상수 flatten
            nested_flatten = extract_flatten_format_from_nested_format(
                nested_format=constant_value,
                root_key_prefix=constant_name,
            )
            flatten_mapping.update(nested_flatten)
            
        # 상수로 선언되지 않으면서 indexed mapping 내부에만 있는 값 처리
        flatten_indexed_mapping = {}
        for key, value in indexed_mapping.items():

            # 상수로 선언된 값들은 위의 로직에서 처리 됐을 것이므로, mapped constants 에 없는 값들만 추출하여 적용
            if key in mapped_constants.values():
                continue

            flatten_indexed_mapping.update(
                extract_flatten_format_from_nested_format(
                    nested_format=value,
                    root_key_prefix=key,
                )
            )

        # 상수로 선언되지 않으면서 indexed mapping 내부에만 있는 값 적용
        flatten_mapping.update({
            k: v for k, v in flatten_indexed_mapping.items()
            if k not in flatten_mapping
        })

        return flatten_mapping

    @classmethod
    def get_ordered_flatten_constants_value(cls) -> list[str]:
        """
        해당 attribute schema 가 가지고 있는 상수 값 전체의 
        순서가 보장되면서 flatten 한 컬럼명 정보 반환

        주의 사항
        - 컬럼 순서는 기본적으로 attribute schema 에 선언된 상수의 순서를 기반하며
          get_flatten_constants_name_value_mapping() 이 어느 정도 순서를 보장하므로 
          일반적인 경우 해당 메서드를 그대로 이용
          
          단, indexed 컬럼처럼 특수한 컬럼에 대해 컬럼 순서 조정이 필요한 경우,
          개별 상속 클래스가 구현의 책임을 가지고 해당 메서드를 오버라이딩 해야 함

        - 추가적인 컬럼 순서 조정이 필요 없는 경우 pass

        :return: flatten 및 ordered 된 컬럼명 정보 (상수 값) list[str]
        """

        return list(cls.get_flatten_constants_name_value_mapping().values())
