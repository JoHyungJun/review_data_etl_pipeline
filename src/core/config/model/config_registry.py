"""
config_registry.py
------------------

스키마 및 설정값 관리를 위한 Section-based configuration 구조의 데이터 저장소 클래스 모듈

내부 변수 _merged_schema (dict[str, Section]) 를 통해 설정값이 save 및 관리되며,
내부 메서드 get_value() 및 Section/Option 명을 통해 설정값에 접근할 수 있음
"""


from typing import Optional, Any

from core.config.model.config_base_section_option import Section
from core.config.util.config_util import get_singleton_schema, merge_schema_with_config


class ConfigRegistry:
    """
    스키마 및 외부 설정값을 통합하여 save 및 관리하는 클래스

    내장된 싱글톤 스키마를 기반으로
    요청 단위마다 설정된 외부 설정값을 덮어 써서 병합하고 관리하며,
    실행 시점에 유효 설정값을 검증하고 반환
    """

    def __init__(self, section_based_config_dict: Optional[dict[str, Section]] = None):
        self._yaml_schema = get_singleton_schema()
        self._config_data = section_based_config_dict or {}
        self._merged_schema = merge_schema_with_config(
            section_based_schema_dict=self._yaml_schema,
            section_based_config_dict=self._config_data
        )

    def has_config_data_section(self, section_key: str) -> bool:
        """
        외부 설정값에서 파라미터에 해당하는 section 의 존재 여부 반환

        주의 사항
        - 해당 메서드는 외부 설정값에 대상 section 데이터가 들어왔는지 검증하는 메서드이며,
          기본 schema 와 결합되지 않은 raw 외부 설정값에서의 section 존재 여부를 반환함

        :param section_key: 조회 대상 Section 명
        :return: 해당 section 의 존재 여부 bool
        """

        return self._config_data.get(section_key) is not None


    def get_value(self, section_key: str, option_name: str, use_default_value: bool = False) -> Optional[Any]:
        """
        스키마 및 외부 설정값이 병합된 설정값에서 Section/Option 명으로 값 조회 및 반환

        파라미터로 입력된 Section/Option 명이 존재하지 않는 경우 KeyError 를 발생시키며,
        따라서 해당 메서드 호출 시 하드코딩 및 오탈자 방지를 위해 schema_constants.py 의 상수 활용을 권고

        :param section_key: 조회 대상 Section 명
        :param option_name: 조회 대상 Option 명
        :param use_default_value: 기본값 사용 여부
        :return: Option 의 get_effective_value() 반환값 Optional[Any]
        """

        section_data = self._merged_schema.get(section_key)
        if section_data is None:
            raise KeyError(f"{section_key} 섹션이 존재하지 않습니다. 설정 파일을 확인해주세요.")

        option = section_data.options.get(option_name)
        if option is None:
            raise KeyError(f"{section_key}.{option_name} 옵션이 존재하지 않습니다. 설정 파일을 확인해주세요.")

        return option.get_effective_value(use_default_value)
