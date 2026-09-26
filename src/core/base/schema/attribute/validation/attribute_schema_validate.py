"""
attribute_schema_validate.py
----------------------------

attribute schema 관련 컬럼 및 데이터 규칙 검증 모듈
"""


from typing import Type

from core.base.schema.attribute.base_order_history_attribute_schema import BaseOrderHistoryAttributeSchema
from core.base.schema.attribute.base_review_attribute_schema import BaseReviewAttributeSchema


def validate_datetime_fields(attribute_schema: Type[BaseReviewAttributeSchema]) -> None:
    """
    리뷰 작성 시간 관련 컬럼 검증

    리뷰 작성 일시 (DATETIME) / 리뷰 작성 날짜 (DATE) + 리뷰 작성 시간 (TIME)
    둘 중 한쪽은 반드시 초기화 되어야 함을 검증

    :param 검증 대상 BaseAttributeSchema
    """

    datetime_exists = attribute_schema.REVIEW_CREATED_DATETIME not in (None, NotImplemented)

    date_exists = attribute_schema.REVIEW_CREATED_DATE not in (None, NotImplemented)
    time_exists = attribute_schema.REVIEW_CREATED_TIME not in (None, NotImplemented)
    date_and_time_exists = date_exists and time_exists

    if not (datetime_exists or date_and_time_exists):
        raise ValueError(
            f"{attribute_schema.__name__} 스키마에서 리뷰 작성 일시, 리뷰 작성 일자 + 시간이 모두 초기화 혹은 선언되지 않았습니다. 코드를 확인해주세요."
        )


def validate_order_id_dependency(
    review_schema: Type[BaseReviewAttributeSchema],
    order_history_schema: Type[BaseOrderHistoryAttributeSchema],
) -> None:
    """
    주문 id 컬럼 관련 의존성 검증

    주문 내역 데이터와 리뷰 데이터는 주문 id (ORDER_ID) 를 통해 merge/join 되기 때문에
    두 attribute schema 모두 주문 id 컬럼이 초기화 되어야 함을 검증
    """

    review_order_id_exists = review_schema.ORDER_ID not in (None, NotImplemented)
    order_history_order_id_exists = order_history_schema.ORDER_ID not in (None, NotImplemented)

    if not (review_order_id_exists and order_history_order_id_exists):
        raise ValueError(
            f"리뷰 데이터와 주문 내역 데이터를 통합하려면 {review_schema.__name__} 스키마와 {order_history_schema.__name__} 모두에서 "
            f"주문 id (ORDER_ID) 컬럼이 초기화되어야 합니다. "
            f"코드를 확인해주세요."
        )
