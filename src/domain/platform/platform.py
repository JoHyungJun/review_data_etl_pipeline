"""
platform.py
-----------

플랫폼별 기초 정보를 정의한 Enum 모듈

플랫폼의 영어/한글 이름 정보를 관리하며, 시스템 내에서 개별 플랫폼을 식별할 수 있는 id 값을 관리함
플랫폼별 config 정보 등에서 활용

주의 사항
- platform id 값의 경우 식별 정보로, 외부 설정값 비교 등에서 활용되기 때문에,
  해당 플랫폼 관련 로직이 외부 설정값에서 정보를 추출한다면 section key 값을 부여하길 권고
"""


from enum import Enum

from config.constant.name_constants import (
    ABLY_ENG_NAME,
    ABLY_KOR_NAME,
    COUPANG_ENG_NAME,
    COUPANG_KOR_NAME,
    VREVIEW_ENG_NAME,
    VREVIEW_KOR_NAME,
    ABLY_SECTION_KEY,
    COUPANG_SECTION_KEY,
    VREVIEW_SECTION_KEY,
)


class Platform(Enum):

    ABLY = (ABLY_ENG_NAME, ABLY_KOR_NAME, ABLY_SECTION_KEY)
    COUPANG = (COUPANG_ENG_NAME, COUPANG_KOR_NAME, COUPANG_SECTION_KEY)
    VREVIEW = (VREVIEW_ENG_NAME, VREVIEW_KOR_NAME, VREVIEW_SECTION_KEY)

    def __init__(self, eng_name: str, kor_name: str, platform_id: str):
        self._platform_eng_name = eng_name
        self._platform_kor_name = kor_name
        self._platform_id = platform_id

    def get_platform_eng_name(self) -> str:
        return self._platform_eng_name

    def get_platform_kor_name(self) -> str:
        return self._platform_kor_name

    def get_platform_id(self) -> str:
        return self._platform_id
