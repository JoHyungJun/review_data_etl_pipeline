"""
serializer.py
-------------

감성 추론 로깅에서 사용되는 데이터 객체 직렬화/역직렬화 모듈
"""


from dataclasses import is_dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, get_type_hints, Optional, Union

import torch

from util.json_util import try_parse_json


def serialize_log_value(value: Any) -> Any:
    """
    직렬화 대상 value 에 대해 JSON 직렬화 가능 형태로 파싱 후 반환

    주의 사항
    - 해당 메서드의 로직은 BaseSentimentLog model 구성에 대해 강한 결합도를 가지고 있으므로,
      관련되지 않은 다른 호출부에서의 사용에 주의를 권고
      추가적인 class type 에 대한 사용이 필요한 경우 해당 메서드의 수정을 권고

    :param value: 직렬화 포맷팅 대상 값 Any
    :return: JSON 직렬화 가능 포맷으로 파싱된 값 Any
    """

    if is_dataclass(value):
        return {
            k: serialize_log_value(v)
            for k, v in asdict(value).items()
        }

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, Path):
        return str(value)

    if isinstance(value, torch.device):
        return str(value)

    if isinstance(value, dict):
        return {
            k: serialize_log_value(v)
            for k, v in value.items()
        }

    if isinstance(value, list):
        return [
            serialize_log_value(v)
            for v in value
        ]

    return value


def deserialize_log_value(value: Any, type_hint: Optional[Any]) -> Any:
    """
    역직렬화 대상 value 에 대해 type hint 형태로 파싱 후 반환

    주의 사항
    - 해당 메서드의 로직은 BaseSentimentLog model 구성에 대해 강한 결합도를 가지고 있으므로,
      관련되지 않은 다른 호출부에서의 사용에 주의를 권고하며,
      추가적인 class type 에 대한 사용이 필요한 경우 해당 메서드의 수정을 권고

    - 역직렬화 과정에서의 파싱은 type hint 에 의존하며,
      만약 type hint 가 None, Any 이거나 Union 과 같이 둘 이상일 경우, 파싱을 포기하고 원 데이터를 그대로 반환
      (단, dict 의 경우 예외적으로 type hint 2 개까지를 허용하며,
       dict[key_type_hint, value_type_hint] 으로 취급, key, value 를 타입 힌트 순서에 따라 따로 파싱)

    - type hint 는 dict, list, enum, primitive 및 Path, torch.device, dataclass 까지만 허용하며,
      일반적인 클래스 type 의 경우 TypeError 를 raise

    - dataclass 파싱의 경우 파라미터 dict 데이터와 dataclass 관리 변수 정보를 엄격히 맞춰야 함
       
    - value 가 None 이거나 type hint 가 None 일 경우, value 를 그대로 반환

    :param value: 역직렬화 파싱 대상 값 Any
    :param type_hint: 역직렬화 파싱 대상 객체 (type_hint) Any
    :return: type hint 로 파싱된 값 Any
    """

    if value is None:
        return None

    if type_hint is None or type_hint is Any:
        return value

    type_hint_origin = getattr(type_hint, "__origin__", None)
    type_hint_args = getattr(type_hint, "__args__", ())

    # Union
    if type_hint_origin is Union:
        # Optional 의 경우 type 이 자동으로 Union[None, XXX] 으로 바뀌므로, 이를 방어
        concrete_types = [
            type_hint_arg for type_hint_arg in type_hint_args
            if type_hint_arg is not type(None)
        ]

        # Optional 내부의 type hint 를 재할당
        if len(concrete_types) == 1:
            type_hint = concrete_types[0]
            type_hint_origin = getattr(type_hint, "__origin__", None)
            type_hint_args = getattr(type_hint, "__args__", ())
        # Optional 내부가 복합 type hint (파싱 포기)
        else:
            return value

    # dict, list 처럼 generic type 만 origin 속성을 가지므로, 이들에 대해서만 type hint 개수 판별
    if type_hint_origin is not None:
        if not type_hint_args or len(type_hint_args) >= 3:
            return value

    value = try_parse_json(value)

    # dict
    if isinstance(value, dict):
        # BaseSentimentLog 기반 (event_type 관련을 처리하기 위함)
        from process.core.postprocess.postprocessing.postprocessor.common.sentiment.log.model.models import BaseSentimentLog
        if isinstance(type_hint, type) and issubclass(type_hint, BaseSentimentLog):
            return BaseSentimentLog.from_dict(value)

        # dataclass
        if is_dataclass(type_hint):
            inner_hints = get_type_hints(type_hint)

            deserialized_dataclass_dict = {
                k: deserialize_log_value(v, inner_hints.get(k, Any))
                for k, v in value.items()
            }
            return type_hint(**deserialized_dataclass_dict)

        # dict[key_type, value_type]
        if len(type_hint_args) == 2:
            key_type_hint, value_type_hint = type_hint_args

            # Union, Any 의 경우 Any 타입으로 치환
            if getattr(key_type_hint, "__origin__", None) is Union or key_type_hint is Any:
                key_type_hint = Any

            if getattr(value_type_hint, "__origin__", None) is Union or value_type_hint is Any:
                value_type_hint = Any

            return {
                deserialize_log_value(inner_key, key_type_hint): deserialize_log_value(inner_value, value_type_hint)
                for inner_key, inner_value in value.items()
            }

        # value 가 dict type 이면서, type hint 가 dict, Any 가 아닐 경우, 명세의 잘못으로 취급, raise
        # (일반 클래스 타입의 경우 역직렬화로 순수한 dict 데이터가 들어옴)
        if isinstance(type_hint, type) and type_hint not in (dict, Any):
            raise TypeError(
                f"역직렬화 실행 도중, 파라미터 type_hint 에 제공되는 파싱 타입이 아닌 '{type_hint.__name__}' 가 선언되었습니다. "
                f"코드를 확인해주세요."
            )

        # 그 외의 경우 (파싱 포기)
        return {
            deserialize_log_value(inner_key, None): deserialize_log_value(inner_value, None)
            for inner_key, inner_value in value.items()
        }

    # list
    if isinstance(value, list):
        # 단일 type hint
        if len(type_hint_args) == 1:
            inner_type_hint = type_hint_args[0]
            return [deserialize_log_value(inner_value, inner_type_hint) for inner_value in value]

        # 복합 type hint (파싱 포기)
        else:
            return [deserialize_log_value(inner_value, None) for inner_value in value]

    # 개별 속성
    if type_hint is datetime and isinstance(value, str):
        return datetime.fromisoformat(value)

    if type_hint is Path and isinstance(value, str):
        return Path(value)

    if type_hint is torch.device and isinstance(value, str):
        return torch.device(value)

    if isinstance(type_hint, type) and issubclass(type_hint, Enum) and not isinstance(value, Enum):
        return type_hint(value)

    # primitive type 혹은 알 수 없는 파싱 타입 value 의 경우 그대로 반환
    return value
