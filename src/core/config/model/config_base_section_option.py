"""
config_base_section_option.py
-----------------------------

스키마 및 설정값 관리를 위한 Section-based configuration 구조의 데이터 단위 클래스 모듈

스키마 및 설정값을 Section, Option 구조를 통해 검증 및 관리하며,
OptionMeta 를 통해 해당 값에 대한 메타 정보를 추가 save
"""


from __future__ import annotations
from inspect import signature
from typing import Union, Optional, Any

from config.constant.data_types import DataType, get_parsed_value_by_data_type
from error.config import ConfigNotAvailableError


class OptionMeta:
    """
    Option 항목의 메타 정보 정의용 클래스

    메타 정보는 스키마 정보에만 포함되는 것으로,
    외부 사용자가 추가한 설정값에 대해서는 메타 정보가 포함되지 않음 (None)

    내장 변수
    - default_value: 해당 설정값이 설정 되지 않았을 때 (None) 활용할 기본값을 의미
    - is_required: 해당 설정값의 호출 시, 해당값이 반드시 필요한 필수값 (None 일 수 없음) 인지에 대한 여부 의미
    - description: 해당 설정값에 대한 설명을 의미
    - data_type: 해당 설정값에 대한 커스텀 자료형을 의미 (DataType Enum 클래스에 정의)

    내장 변수 규칙
    is_required (bool) 과 default_value (기본 설정값) 는 다음과 같은 규칙을 가짐
    - True / O (not None): 로직 수행에 반드시 필요한 값이지만, 별도의 외부 설정 없이도 내장된 default_value 활용
    - True / X (None): 외부 설정 파일에서 반드시 해당 값이 입력되어야 함
    - False / O or X: Optional 값이며, 기본값 사용 여부에 따라 반환 값이 달라짐

    주의 사항
    스키마 코드 혹은 YAML 에 OptionMeta 없이 Option 을 추가했을 경우, 기본 OptionMeta 가 해당 Option 에 부여되는데,
    기본 OptionMeta 인스턴스의 경우 생성자 파라미터가 is_required=True, default_value=None 으로 부여됨
    이 경우 비정상적인 경로로의 변수 생성을 의미하여, 내부 로직 상 해당 Option 의 value 을 반환하려 했을 때 에러를 내게 되므로,
    Option 추가 시 반드시 OptionMeta 설정을 권고
    """

    def __init__(
            self,
            is_required: bool = True,
            default_value: Optional[Union[str, int, float]] = None,
            data_type: DataType = DataType.STR,
            description: str = "",
    ):
        self.default_value = default_value
        self.is_required = is_required
        self.description = description
        self.data_type = data_type

    @classmethod
    def from_dict(cls, meta_dict: dict) -> OptionMeta:
        """
        dict 데이터 기반 OptionMeta 인스턴스 생성 후 반환

        dict 에서 OptionMeta 내장 변수와 같은 이름의 key 만을 추출하여
        OptionMeta 내장 변수를 초기화 및 반환

        :param meta_dict: OptionMeta 인스턴스 초기화에 활용할 데이터 dict
        :return: 초기화된 인스턴스 OptionMeta
        """

        sig = signature(OptionMeta)
        init_kwargs = {
            k: meta_dict.get(k) for k in sig.parameters if k in meta_dict
        }

        return OptionMeta(**init_kwargs)


class Option:
    """
    단일 설정값을 관리하는 클래스

    value 를 파싱하고, 유효 value 를 반환하는 메서드를 포함

    내장 변수
    - key: 해당 설정값의 key 를 의미
    - value: 해당 설정값의 value 를 의미
    - meta: 해당 설정값의 메타 정보를 의미
    """

    def __init__(
            self,
            key: str,
            value: Optional[Union[str, int, float]] = None,
            meta: OptionMeta = None,
    ):
        self.key = key
        self.value = None
        self.meta = meta

        if self.meta is not None and value is not None:
            self.set_value(value)
        else:
            self.value = value

    def set_value(self, raw_value: Optional[Union[int, float, str]]) -> None:
        """
        입력값 raw_value 를 파싱 및 내장 value 에 설정

        :param raw_value: value 에 부여할 설정값
        :return: 없음
        """

        if self.meta is None:
            return

        self.value = get_parsed_value_by_data_type(raw_value, self.meta.data_type)

    def get_effective_value(self, use_default_value: bool = False) -> Optional[Any]:
        """
        내장된 value 에 대해 검증 및 유효한 value 를 반환

        단순 내장 value 를 반환하는 것이 아닌,
        내장된 OptionMeta 의 메타 정보 및 파라미터의 기본값 사용 여부 정보를 활용하여
        유효성을 검증하고 조건에 맞는 value 를 반환

        유효값 반환 로직 규칙은 OptionMeta 의 is_required/default_value 규칙을 따르되,
        단, 파라미터의 use_default_value 가 is_required 보다 default_value 사용 여부 강제력에 우선 순위를 가짐

        :param use_default_value: 기본값 사용 여부
        :return: 검증된 유효 value Optional[Any]
        """

        # 내장 value 가 존재할 경우 바로 반환
        if self.value is not None:
            return self.value

        # 메타 정보가 없다는 의미는, 외부 수정에 의해 Section/Option key 까지만 선언되고 value 가 없는 케이스
        # 사용자가 일부러 값만 비워뒀을 수 있으므로 None 반환
        if self.meta is None:
            return None

        # 내장 value 가 없기 때문에 기본 값 사용 여부를 확인
        # 기본값 사용 여부가 스키마의 is_required 보다 우선됨
        if use_default_value:
            # 해당 value 가 호출부 로직에서 반드시 필요한 필수값이지만, 기본값 마저 존재하지 않는다면 에러
            if self.meta.is_required and self.meta.default_value is None:
                raise ConfigNotAvailableError(
                    f"필수 항목 {self.key} 의 설정/기본 값이 모두 존재하지 않습니다. 설정 파일을 확인해주세요."
                )

            return self.meta.default_value

        # 해당 변수가 필수값임에도 설정된 값이 없고, 기본값도 사용하지 않는다면 에러
        if self.meta.is_required:
            raise ConfigNotAvailableError(
                f"필수 항목 {self.key} 의 설정값이 없으면서 기본값 사용을 불허용하고 있습니다. 설정 파일 및 코드를 확인해주세요."
            )

        # 해당 변수가 필수값이 아니라면 None 반환 (의도적인 Optional 항목)
        return None


class Section:
    """
    설정값 (Option) 들의 카테고리별 그룹 정보를 관리하는 클래스

    해당 Section 의 하위 Option 들을 검증 및 save 하고 관리

    내장 변수
    - name: 해당 Section 의 이름을 의미
    - options: 해당 Section 하위 Option 들의 모음 dict 의미
    """

    def __init__(self, key: str):
        self.key = key
        self.options: dict[str, Option] = {}

    def add_option(self, option: Option) -> None:
        """
        해당 Section 하위의 개별 Option 을 부여

        :param option: 해당 Section 하위에 부여할 대상 Option
        :return: 없음
        """

        self.options[option.key] = option

    def get_option(self, option_key: str) -> Option:
        """
        파라미터로 입력된 Option name 에 해당하는, 해당 Section 하위의 Option 반환

        :param option_key: 대상 Option 의 key
        :return: 파라미터 입력에 해당하는 key 의 Option
        """
        
        if option_key not in self.options:
            raise KeyError(f"{option_key} 옵션은 '{self.key}' 섹션에 존재하지 않습니다. 설정 파일을 확인해주세요.")

        return self.options[option_key]
