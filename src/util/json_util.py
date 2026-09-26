"""
json_util.py
------------

json 데이터 포맷팅/추출/전처리 관련 util 모듈
"""


import json
import logging
import re

from typing import Union, Any


def try_parse_json(value: Any) -> Any:
    """
    하나의 문자열로 감싸진 json (dict) 포맷을 정상적인 dict 형태로 파싱 후 반환

    특정 API 의 경우, 특정 value 가 dict 구조를 하나의 문자열로 가지고 있는 케이스가 있음
    (ex. {"nested_key": "{\"A\":{\"B\":\"C\"}}"})
    이런 경우에도 정상적인 구조로의 파싱을 위해 활용

    :param value: 파싱 대상 value
    :return: 파싱된 dict 형태의 json 인스턴스 또는 원본 value
    """

    # str 이 아니라면 파싱이 불필요하므로, 로직 미적용
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed
        except (json.JSONDecodeError, TypeError):
            return value

    return value


def extract_flat_values_from_json(data: Any, prefix: str = "") -> Any:
    """
    nested (dict) 한 구조의 json 데이터를, flat 형태의 단순 구조로 파싱 후 반환

    json 처럼 하나의 key 가 dict, list 등 여러 형태의 자료를 가질 수 있는 구조는
    Excel 처럼 하나의 key 가 단일 원소 value 를 갖는 구조와 매핑될 수 없으므로,
    단일 key 가 단일 원소 value 에 매핑될 수 있도록 key 명에 네이밍 규칙을 적용하여 개별 원소에 파싱

    파싱 규칙
    - 중첩 dict 구조의 경우, 단일 원소를 만날 때까지 재귀 탐색
    - list 구조의 경우, 단일 원소는 네이밍 규칙이 적용된 개별 key 와 일대일 대응

    key 명 네이밍 규칙
    - 중첩 dict 구조의 경우, 단일 원소까지의 재귀 탐색 중 만난 key 를 순서대로 적어 최종 key 를 완성하며,
      탐색 중 만난 개별 key 는 구분자 '.' 를 통해 분리됨
      (ex. "json.response.data" = "list")
    - list 구조의 경우, 해당 list 기준 개별 원소의 index 를 마지막에 붙여 최종 key 를 완성하며,
      index 값의 경우 구분자 '.' 를 통해 분리됨
      (ex. "list.1" = "A", "list.2" = "B")
    - dict 와 list 가 혼합된 구조의 경우에도 단일 원소까지 재귀 탐색하며, 같은 규칙을 혼용하여 적용함
      (ex. "json.response.data.list.1" = "A")

    :param data: 파싱 대상 nested 구조의 data
    :param prefix: 최종 key 생성을 위한 재귀 탐색용 prefix
    :return: flat 구조로 파싱된 data
    """

    flat = {}

    for key, value in data.items():
        full_key = f"{prefix}{key}"

        # 하나의 문자열로 감싸진 json (dict) 포맷 검증 및 파싱
        value = try_parse_json(value)

        # value 가 dict 구조일 경우 재귀 탐색
        if isinstance(value, dict):
            flat.update(extract_flat_values_from_json(value, f"{full_key}."))

        # value 가 list 구조일 경우 index 를 이용한 key 명 네이밍 규칙 적용
        elif isinstance(value, list):
            for i, item in enumerate(value, start=1):
                if isinstance(item, dict):
                    flat.update(extract_flat_values_from_json(item, f"{full_key}.{i}."))
                else:
                    flat[f"{full_key}.{i}"] = clean_illegal_char(item)

        # 일반 value 의 경우 정상적이지 않은 문자를 제외 후 save
        else:
            flat[full_key] = clean_illegal_char(value)

    return flat


def clean_illegal_char(value: Any) -> Any:
    """
    Excel save 에 문제가 발생할 만한 비정상적인 문자 제거 후 반환

    :param value: save 대상 개별 data
    :return: 비정상적인 문자가 제거된 data str 또는 원본 value
    """

    # str 이 아니라면 파싱이 불필요하므로, 로직 미적용
    if isinstance(value, str):
        return re.sub(r"[\x00-\x1F\x7F]", "", value.replace("\n", " "))

    return value


def build_record(flat_data: dict, target_keys: list[str]) -> dict:
    """
    [WARN] Deprecated

    이 메서드는 리팩토링 중 다음과 같은 이유로 효용성이 떨어진다고 판단,
    더 이상 사용하지 않게 되었습니다.

    - 로그 처리만을 위한 메서드
    - 메인 프로세스와 분리되어, 추가적인 로그 처리에 과도한 파라미터 추가가 일어남
    - 반환 값에 대한 로직이 짧음
      (메인 프로세스 구조 변경에 따라 반환 값이 list -> dict 으로 변경)

    단, 엣지 케이스에 대한 docstring 정보 유지를 위해 임시로 해당 메서드를 유지합니다.

    -----------------------------------------------------------------

    파싱된 flat 구조의 전체 데이터로부터 특정 대상 데이터 추출 및 순서가 유지된 Excel 행 리스트 생성

    - target_keys 에 해당하는 key 의 데이터만 추출
    - target_keys 의 key 중 flat_data 에 존재하지 않는 key 가 있다면 로그 처리

    주의 사항
    - flat_data 의 list 데이터의 경우, 개별 API json response 데이터마다 list 개수가 유동적인데 반해,
      target_keys 는 save 포맷이기 때문에 정확한 추출 대상 key 전체가 명시되어야 하므로 불일치 가능성이 생김
      
      (ex. flat_data 중 'data_1' 라는 데이터의 "A" list 에 원소가 하나밖에 없다면 ("data_1.A": [1])
           flat_data.data_1.keys() = ["A.1"] / target_keys = ["A.1", "A.2", "A.3"]
           이때, 'data_1.A' 는 단순히 하나의 데이터만 가지고 있을 뿐 정상 데이터임에도 불구하고
           A.2, A.3 의 key 가 존재하지 않아 missing_keys 의 대상이 됨)

      따라서 flat_data 및 target_keys 의 모든 key 에 대해 list index 숫자를 특정 문자열 ("{index"}) 으로 치환하고
      개별 key 존재 여부를 단순 탐색으로 찾아 탐색 속도를 줄임

      이때 list index 판별 기준은 key 양쪽 끝, 혹은 '.' 으로 둘러 싸인 단순 숫자를 기준하며, (ex. "A.1", "1.A", "A.1.B")
      따라서 특정 key 명이 순수 숫자일 경우 구분 불가

    - flat_data 중 특정 key 의 부모 key 가 모두 None 이라면 missing_keys 의 대상이 될 수 있음

      (ex. API 포맷이 {"A": {"B": "value"}} 이라고 가정했을 때, 포맷에 따라 target_keys 에는 "A.B" 가 들어갈 수 있지만,
           특정 flat_data 의 A 데이터가 None 이라면 {"A": None} 이 되어버리고
           flat_data.keys() None 으로 인해 "A.B" 까지의 탐색이 안 되어 "A" key 만 존재)

    - json response 가 key 없이 list 로 시작하는 케이스는 배제 (ex. response = {["A"], ["B"]}

    - 앞서 설명한 edge case 들로 인해 missing_keys 탐색 로직은 완벽하지 않고, 따라서 missing_keys 로그는 단순 참고만을 권고

    :param flat_data: flat 구조로 파싱된 data dict
    :param target_keys: 추출 대상 및 Excel 열 순서 기준이 되는 key list
    :return: 최종 추출된 data dict
    """

    # flat_data 의 개별 key 변환 (list index 숫자 -> '{index}') 후 set save
    flat_keys_set = {
        re.sub(r'\.(\d+)(\.|$)', r'.{index}\2', k)
        for k in flat_data.keys()
    }

    missing_keys = []
    for key in target_keys:
        # 개별 target key 변환 (list index 숫자 -> '{index}')
        key_pattern = re.sub(r'\.(\d+)(\.|$)', r'.{index}\2', key)

        # 단순 탐색
        if key_pattern not in flat_keys_set:
            missing_keys.append(key)

    if missing_keys:
        logging.warning(
            f"[MERGE] process=build_record, missing_keys={missing_keys}: Found missing keys in API response data "
            f"- keys are not in API response, or mismatched format"
        )

    # 하나의 json 데이터 (dict) 에서 target keys 에 해당하는 데이터만 추출
    return {
        key: flat_data.get(key, "")
        for key in target_keys
    }


def extract_target_data(
        data: Union[dict[str, Any], list[dict[str, Any]]],
        json_target_data_path: list[Union[str, Any]]
) -> list[dict]:
    """
    타겟 데이터를 재귀 key 탐색을 통해 접근

    API 마다 관심 대상 데이터를 담는 구조와 key 가 다르므로,
    타겟 데이터에 대한 접근 key 순서 list 를 기반으로 (JSON_TARGET_DATA_PATH) 재귀 탐색하여
    관심 대상 데이터를 담은 list 반환

    (ex. API 포맷이 {"datas": "reviews": [ {"review_id": 1, ...}, {"review_id": 2, ...} ]} 라 가정하면,
         타겟 데이터는 개별 review 이고, 따라서 전체 review 를 담은 "reviews" 가 타겟 데이터의 상위 key 가 되며,
         따라서 json target data path 는 ["datas", "reviews"] 가 됨)

    :param data: nested 구조의 dict
    :param json_target_data_path: 타겟 데이터의 접근 key 순서
    :return: 관심 대상 데이터만 담긴 List[dict]
    """

    failed_key = None
    for key in json_target_data_path:
        # dict 라면 아직 최종 list 에 도달하지 못했으므로 재귀 탐색
        if isinstance(data, dict):
            data = data.get(key, {})

        # list 라면 1-based indexing 변환 후 재귀 탐색
        elif isinstance(data, list):
            try:
                key_int = int(key)
                data = data[key_int - 1]
            except (ValueError, IndexError):
                failed_key = key
                data = []
                break
        else:
            failed_key = key
            data = []
            break

    if failed_key is not None:
        logging.warning(
            f"[FAILED] process=extract_target_data, failed_key={failed_key}: "
            f"While found target key"
        )

    return data


def reverse_dict_key_value(target_dict: dict) -> dict:
    """
    대상 dict 의 key 와 value 를 뒤바꾸어 변환 후 반환

    :param target_dict: 변환 대상 dict
    :return: 변환된 dict
    """

    return {v: k for k, v in target_dict.items()}
