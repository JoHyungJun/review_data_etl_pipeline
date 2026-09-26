"""
source_data_context.py
----------------------

preprocessing 에서 데이터 수집에 사용된 전체 데이터 및 컬럼명으로 활용되는 개별 schema (prefixed) 정의 모듈

파이프라인의 규칙에 의해 특정 attribute schema 는 None 이 될 수 있으며,
이에 대한 validate 및 처리에 대한 책임은 개별 호출부가 가짐

해당 클래스가 관리하는 개별 변수에 대한 정보는 다음과 같음

- review_attribute_schema:
    리뷰 컬럼명 정보 관련 Type[BaseReviewAttributeSchema]

- product_id_mapping_attribute_schema:
    상품 id 매핑 컬럼명 정보 관련 Type[BaseProductIdMappingAttributeSchema]

- product_option_mapping_attribute_schema:
    상품 정보 매핑 컬럼명 정보 관련 Type[BaseProductOptionMappingAttributeSchema]

- order_history_attribute_schema (Optional):
    주문 내역 컬럼명 정보 관련 Optional[Type[BaseOrderHistoryAttributeSchema]]

- joined_df:
    개별 schema 에 선언된 컬럼명 정보 기반
    review, order history (Optional), product id mapping, product option mapping 네 가지 데이터를 모두 가지고 있는 pandas.DataFrame
"""


from typing import Type, Optional

import pandas
from dataclasses import dataclass

from core.base.schema.attribute.base_order_history_attribute_schema import \
    BaseOrderHistoryAttributeSchema
from core.base.schema.attribute.base_product_id_mapping_attribute_schema import \
    BaseProductIdMappingAttributeSchema
from core.base.schema.attribute.base_product_option_mapping_attribute import \
    BaseProductOptionMappingAttributeSchema
from core.base.schema.attribute.base_review_attribute_schema import \
    BaseReviewAttributeSchema


@dataclass(frozen=True)
class SourceDataContext:

    joined_df: pandas.DataFrame

    review_attribute_schema: Type[BaseReviewAttributeSchema]
    product_id_mapping_attribute_schema: Type[BaseProductIdMappingAttributeSchema]
    product_option_mapping_attribute_schema: Type[BaseProductOptionMappingAttributeSchema]

    order_history_attribute_schema: Optional[Type[BaseOrderHistoryAttributeSchema]] = None

    def unpack(self):
        """
        해당 클래스가 관리하는 모든 변수를 하나의 tuple 로 반환

        반환 순서는 다음과 같음
        1. review_attribute_schema
        2. order_history_attribute_schema
        3. product_id_mapping_attribute_schema
        4. product_option_mapping_attribute_schema
        5. joined_df

        :return: 해당 클래스가 관리하는 모든 변수를 가진
                 tuple[
                    review_attribute_schema,
                    order_history_attribute_schema,
                    product_id_mapping_attribute_schema,
                    product_option_mapping_attribute_schema,
                    joined_df
                 ]
        """

        return (
            self.review_attribute_schema,
            self.order_history_attribute_schema,
            self.product_id_mapping_attribute_schema,
            self.product_option_mapping_attribute_schema,
            self.joined_df,
        )
