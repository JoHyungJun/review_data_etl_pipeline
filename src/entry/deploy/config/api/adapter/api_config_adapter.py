"""
api_config_adapter.py
---------------------

BaseSectionBasedConfigAdapter 형태의 외부 설정값 API 로부터 데이터를 추출하여
dict[str, Section] 구조로 반환하는 클래스 모듈
"""


from pydantic import BaseModel

from core.base.adapter.base_section_based_config_adapter import BaseSectionBasedConfigAdapter
from core.config.constant.schema_constants import COMMON
from core.config.model.config_base_section_option import Section, Option
from entry.deploy.config.api.dto.base.base_api_request import BaseApiRequest


class ApiConfigAdapter(BaseSectionBasedConfigAdapter):

    @classmethod
    def load_to_section_based_dict(
            cls,
            request: BaseApiRequest,
    ) -> dict[str, Section]:
        """
        BaseApiRequest 포맷으로 request 요청된 API 에 작성된 설정값 load 및
        Section-based 구조의 dict 으로 반환

        API 는 반드시 해당 메서드의 파싱 로직 포맷대로 작성되어야 함

        주의 사항
        - common_config 는 COMMON Section 으로 변환
        - configs 는 전달된 Section-based configuration 구조로 변환
        - 그 외 추가 변수는 {key (변수명): dict[key, value]} 데이터를
          각각 Section key, Option key, Option value 으로 취급하고 변환
        - Option 의 value 는 문자열로 변환하며, None은 그대로 유지함
        - 동일한 key 의 데이터가 존재할 경우, 최초 이후의 데이터는 무시

        :param request: request 요청된 API 객체 BaseApiRequest
        :return: 파싱된 Section 명이 key 가 되는 dict[str, Section]
        """

        api_dict = {}

        common_section = Section(COMMON.SECTION_KEY)

        # common config 데이터 추출
        for option_name, option_value in request.common_config.model_dump().items():
            common_section.add_option(
                Option(
                    key=option_name,
                    value=(
                        None
                        if option_value is None
                        else str(option_value)
                    ),
                )
            )

        api_dict[COMMON.SECTION_KEY] = common_section

        # configs 데이터 추출
        for section_name, options_dict in request.configs.items():

            # 이미 존재하는 key 와 동일한 key 의 데이터가 들어왔을 경우 무시
            section_name = str(section_name)
            if section_name in api_dict:
                continue

            section = Section(section_name)

            for option_name, option_value in options_dict.items():
                section.add_option(
                    Option(
                        key=str(option_name),
                        value=(
                            None
                            if option_value is None
                            else str(option_value)
                        ),
                    )
                )

            api_dict[section_name] = section

        # 추가 변수 데이터 추출
        common_config = request.common_config
        configs = request.configs

        for field_name in type(request).model_fields:
            field_value = getattr(request, field_name)

            # common config / configs 를 제외한 변수 순회
            if field_value is common_config or field_value is configs:
                continue

            # 이미 존재하는 key 와 동일한 key 의 데이터가 들어왔을 경우 무시
            if field_name in api_dict:
                continue

            # 객체 형태일 경우 dump
            if isinstance(field_value, BaseModel):
                field_value = field_value.model_dump()

            # dict 형태가 아닌 데이터의 경우 무시
            if not isinstance(field_value, dict):
                continue

            section = Section(field_name)
            for option_name, option_value in field_value.items():
                section.add_option(
                    Option(
                        key=str(option_name),
                        value=(
                            None
                            if option_value is None
                            else str(option_value)
                        ),
                    )
                )
            api_dict[field_name] = section

        return api_dict
