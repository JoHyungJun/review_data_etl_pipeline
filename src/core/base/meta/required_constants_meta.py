"""
required_constants_meta.py
--------------------------

RequiredConstantsMeta 클래스를 메타 클래스로 선언하였을 때, 해당 클래스를 상속하는 클래스들은
NotImplemented 으로 선언된 상수들을 반드시 초기화 해야 하는 강제성을 부여하는 메타 클래스

대상이 되는 상수들은 상수명이 대문자와 특수문자로만 작성되었다고 전제 (isupper() == True)

하위 클래스에서 NotImplemented 으로 선언된 상수를 초기화하지 않을 시, 클래스 생성 시점에 TypeError 를 발생
"""


class RequiredConstantsMeta(type):

    def __init__(cls, name, bases, namespace):
        super().__init__(name, bases, namespace)

        # 선언된 클래스를 상속하는 전체 자식 클래스 대상
        for base in cls.__mro__[1:-1]:
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

                if value is NotImplemented:
                    if getattr(cls, attr, NotImplemented) is NotImplemented:
                        raise TypeError(
                            f"{cls.__name__} 클래스가 상수 '{attr}' 을/를 초기화 하지 않았습니다. 코드를 확인해주세요."
                        )
