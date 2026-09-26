"""
base_order_history_attribute_schema.py
--------------------------------------

주문 내역 (Order History) 데이터의 공통 컬럼 규칙을 정의하는 추상 클래스 모듈

해당 클래스에 정의된 상수들의 경우 다음과 같은 규칙을 따름

- 각 상수에 초기화된 값은 실제 데이터 단위에서의 컬럼명을 의미하며,
  플랫폼별 API scraping 데이터의 각 key 에 매핑될 컬럼명을 해당 상수에 매핑하여 초기화해야 함
  (추가적인 데이터 저장이 요구되는 경우, 자식 클래스에서 추가적인 상수 선언 및 초기화하여 확장 가능)

- 동일한 상수명을 기준으로 build_attribute_mapping() 메서드를 활용하여
  다른 attribute schema 간 컬럼 rename 이 가능

- NotImplemented 로 선언된 상수는 다음과 같은 의미를 가지며, 따라서 반드시 초기화하여야 함
    - 해당 scraping 에서 필수적으로 요구되는 데이터
    - preprocessing.py 의 전처리 과정에서 반드시 필요한 공통 컬럼명
      (단, 특정 상수의 경우 None 으로 선언 되었더라도, 특정 규칙에 의해 validation 검증이 요구될 수 있음)

- 현재 클래스에서 정의된 상수 및 부모 클래스에서 상속 받은 상수들은 반드시 서로 다른 값을 가지고 있어야 함
  (None, NotImplemented 제외)

자세한 상수 선언 및 활용 규칙은 BaseAttributeSchema 의 docstring 참고
"""


from core.base.schema.attribute.base_attribute_schema import BaseAttributeSchema


class BaseOrderHistoryAttributeSchema(BaseAttributeSchema):

    # required & preprocessing
    ORDER_ID: str = NotImplemented
    PRODUCT_ID: str = NotImplemented

    # optional
    BUYER_NAME: str = None
    BUYER_PHONE: str = None
    BUYER_EMAIL: str = None
