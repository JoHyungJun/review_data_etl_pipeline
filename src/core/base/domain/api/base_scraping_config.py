"""
base_scraping_config.py
-----------------------

스크래핑 관련 정보 관리의 기반이 되는 추상 클래스 설정 모듈

- BaseApiConfig 를 상속하여 API 관련 필수 설정 구현 강제
"""


from abc import abstractmethod
from typing import Optional

from core.base.domain.api.base_api_config import BaseApiConfig
from util.datetime_util import adjust_term_to_safe_limit_ms
from util.column_util import extract_flatten_format_from_nested_format


class BaseScrapingConfig(BaseApiConfig):
    """
    스크래핑 관련 정보 관리의 기반 설정 추상 클래스

    - API 호출 정보 (API method, url, header, query params, body 등) 구현 강제
    - output 디렉토리, Excel/JSON 포맷, 사천 처리 매핑 (preprocessing mapping) 구현 강제
    - 스크래핑 시 재시도 횟수 (max_retries) 와 요청 간 딜레이 (delay_seconds) 설정 강제
    - 플랫폼에서 제한한 최대 스크래핑 기한 (get_scrap_term_limit_ms) 구현 강제
    """

    @abstractmethod
    def get_scraping_start_date(self) -> str:
        pass

    @abstractmethod
    def get_scraping_start_time(self) -> Optional[str]:
        pass

    @abstractmethod
    def get_scraping_end_date(self) -> str:
        pass

    @abstractmethod
    def get_scraping_end_time(self) -> Optional[str]:
        pass

    @abstractmethod
    def get_scraping_term_limit_ms(self) -> Optional[int]:
        """
        [WARN] 내부용 메서드

        플랫폼 별 정책 상으로 수집 가능한 기한 반환
        ms 값으로 반환하며, 기한이 무제한이라면 None 반환

        명시된 수집 가능 기한이 1달, 1년 등으로 일 수 단위 기준에 명확하지 않을 수 있으므로,
        해당 메서드보다 get_scrap_safe_term_limit_ms 메서드 사용을 권장함

        :return: 정수의 milli seconds 값 Optional[int]
        """

        pass

    def get_scraping_safe_term_limit_ms(self) -> Optional[int]:
        """
        플랫폼 별 정책 상으로 수집 가능한 기한 (get_scrap_term_limit_ms) 보다 작은
        약 80% 의 안전한 기한을 반환하는
        ms 값으로 반환하며, 기한이 무제한이라면 None 반환

        명시된 수집 가능 기한이 1달, 1년 등으로 일 수 단위 기준에 명확하지 않을 수 있으므로,
        get_scrap_term_limit_ms 메서드보다 해당 메서드 사용을 권장함

        :return: 정수의 milli seconds 값 Optional[int]
        """

        return adjust_term_to_safe_limit_ms(self.get_scraping_term_limit_ms())

    @abstractmethod
    def get_json_format(self) -> dict:
        pass

    @abstractmethod
    def get_json_target_data_path(self) -> list[str]:
        """
        API response 의 json 구조에서 목표하는 데이터의 위치를
        연속적인 json 의 key 배열로 최상단 key 부터 target list 의 key 까지 순차적으로 반환
        (ex. API 포맷이 {"datas": "reviews": [ {"review_id": 1, ...}, {"review_id": 2, ...} ]} 라 가정하면,
             타겟 데이터는 개별 review 이고, 따라서 전체 review 를 담은 "reviews" 가 타겟 데이터의 상위 key 가 되며,
             따라서 JSON_TARGET_DATA_PATH 는 ["datas", "reviews"] 가 됨)

        호출부에선 해당 정보로 response json 에서 연속 key 탐색을 통해
        실제 데이터 위치에 접근할 수 있음

        :return: 연속적인 key 배열 list[str]
        """

        pass

    @abstractmethod
    def get_json_target_data_pk_name(self) -> str:
        """
        API response 의 target list 에서
        개별 원소들의 식별자 key (pk) 값

        :return: target list 에서 개별 데이터의 식별자 key (pk) 값 str
        """

        pass

    @abstractmethod
    def _get_nested_formant_json_attribute_mapping(self) -> dict:
        """
        [WARN] 내부용 메서드

        해당 플랫폼의 response API 기반으로
        {추출 대상 데이터 key} : {해당 key 에서 변환할 컬럼명} 으로 매핑된 nested dict 반환

        원본 dict 는 작성 시의 편의성을 위한 간소화 버전이므로,
        개별 json key 와 변환할 컬럼명이 일대일 매핑 된 전체 버전의 매핑 정보 dict 이 요구될 때엔
        해당 메서드가 아닌 get_flatten_format_json_attribute_mapping() 메서드 사용이 요구됨

        간소화 매핑 dict 작성 방법
        - 전체 형태는 플랫폼별 API json 형태를 기반하며, 추출할 데이터를 원본 response 구조에 맞게 작성
        - key 에는 API json 의 key 명을, value 에는 변환할 컬럼명을 작성
        - list 데이터의 경우 같은 컬럼명 prefix 를 list 내부에, 최대 반복 횟수를 * 으로 작성
          (flat 형태의 경우 개별 list 원소가 하나의 컬럼이 됨)
        (ex. "reviews": {
                          "review_id": "리뷰_id"
                          "img": ["이미지"] * 3
                        }
        이런 구조일 때, 추출 대상은 API json 에서의 review_id, img (최대 3개) 이고,
        실제 flat 형태로 매핑된 컬럼명은 "리뷰_id", "이미지.1", "이미지.2", "이미지.3" 이 됨)

        :return: raw attribute 명 매핑 dict
        """

        pass

    def get_flatten_format_json_attribute_mapping(self) -> dict:
        """
        해당 플랫폼의 response API 기반으로
        {추출 대상 데이터 key : 해당 key 에서 변환할 컬럼명} 으로 매핑된 flat dict 반환

        원본 dict 는 작성 시의 편의성을 위한 간소화 버전이므로
        _get_nested_formant_json_attribute_mapping() 메서드보다
        일대일 컬럼명 매핑된 dict 를 반환하는 해당 메서드 사용을 권장함

        :return: flatten attribute 명 매핑 dict
        """
        
        return extract_flatten_format_from_nested_format(self._get_nested_formant_json_attribute_mapping())

    def get_mapped_pk_attribute_name(self) -> str:
        """
        해당 플랫폼의 response API 기반으로
        {추출 대상 데이터 key : 해당 key 에서 변환할 컬럼명} 으로 매핑된 flatten dict 에서
        개별 데이터의 pk 로 쓰일 컬럼명 반환

        :return: 매핑된 flatten column 명 기준, pk 로 쓰일 데이터의 컬럼명 str
        """

        return self.get_flatten_format_json_attribute_mapping()[self.get_json_target_data_pk_name()]
