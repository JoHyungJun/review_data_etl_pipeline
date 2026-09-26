"""
unique_value_constants_meta.py
------------------------------

UniqueValueConstantsMeta 클래스를 메타 클래스로 선언하였을 때,
해당 클래스 및 부모 클래스에서 선언된 상수들에 중복 값을 넣을 수 없도록 강제성을 부여하는 메타 클래스

대상이 되는 상수들은 상수명이 대문자와 특수문자로만 작성되었다고 전제 (isupper() == True)

단, 가장 마지막 자식 클래스 기준으로 중복값 여부를 검증하며,
중복값 여부 확인 시, 클래스 생성 시점에 ValueError 를 발생
"""


class UniqueValueConstantsMeta(type):

    def __init__(cls, name, bases, namespace):
        super().__init__(name, bases, namespace)

        constants = {}

        # MRO 기반 (부모 클래스 포함), 부모 -> 자식 순으로 전체 상수 수집
        # 가장 마지막 상속 클래스 기준으로 중복 값의 상수가 있는지 검증을 위함
        for base in reversed(cls.__mro__[:-1]):
            for attr, value in base.__dict__.items():
                # 내부 속성 제외
                if attr.startswith("__"):
                    continue

                # callable (메서드, 클래스) 속성 제외
                if callable(value):
                    continue

                # 관습적인 상수명 규칙으로 상수 필터링
                if not attr.isupper():
                    continue

                if value in (None, NotImplemented):
                    continue

                constants[attr] = value

        value_to_keys = {}

        # hashable 한 value (list, dict) 일 경우 발생할 수 있는 에러 넘기기
        for attr, value in constants.items():
            try:
                value_to_keys.setdefault(value, []).append(attr)
            except TypeError:
                continue

        duplicates = {
            v: ks for v, ks in value_to_keys.items()
            if len(ks) > 1
        }

        if duplicates:
            raise ValueError(
                f"{cls.__name__} 클래스에서 중복 상수 값이 감지 되었습니다. "
                f"해당 클래스, 혹은 부모 클래스의 코드를 확인해주세요. : {duplicates}"
            )
