"""
base_product_option_mapping_attribute_schema.py
-----------------------------------------------

해당 프로젝트의 파이프라인 실행 시 {export 플랫폼의 상품 id - 플랫폼 상품 정보} 필수 매핑 데이터의
필수 컬럼을 정의할 상수 추상 클래스 모듈

해당 클래스에 정의된 상수들의 경우 다음과 같은 규칙을 따름

- 각 상수에 초기화된 값은 실제 데이터 단위에서의 컬럼명을 의미

- 동일한 상수명을 기준으로 build_attribute_mapping() 메서드를 활용하여
  다른 attribute schema 간 컬럼 rename 이 가능

- NotImplemented 로 선언된 상수는 다음과 같은 의미를 가지며, 따라서 반드시 초기화하여야 함
    - 해당 데이터 단위를 활용하는 로직에서 필수적으로 요구되는 데이터
    - preprocessing.py 의 전처리 과정에서 반드시 필요한 공통 컬럼명
      (단, 특정 상수의 경우 None 으로 선언 되었더라도, 특정 규칙에 의해 validation 검증이 요구될 수 있음)

- 현재 클래스에서 정의된 상수 및 부모 클래스에서 상속 받은 상수들은 반드시 서로 다른 값을 가지고 있어야 함
  (None, NotImplemented 제외)

자세한 상수 선언 및 활용 규칙은 BaseAttributeSchema 의 docstring 참고
"""


from core.base.schema.attribute.base_attribute_schema import BaseAttributeSchema


class BaseProductOptionMappingAttributeSchema(BaseAttributeSchema):

    # required & preprocessing
    EXPORT_PLATFORM_PRODUCT_ID: str = NotImplemented

    # optional
    PRODUCT_NAME: str = None
    PRODUCT_OPTION_NAME: str = None
