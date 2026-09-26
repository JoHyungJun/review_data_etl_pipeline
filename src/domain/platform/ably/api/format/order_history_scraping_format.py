"""
order_history_scraping_format.py
--------------------------------

A-bly order history scraping API response 의 json 포맷 모듈

주의 사항
- RESPONSE_JSON_FORMAT 의 경우 response 로 전달되는 전체 json 포맷 및 자료형 매핑 데이터지만,
  스키마 참고용으로만 활용하고 해당 상수의 데이터를 직접 활용하지 않는 것을 권고
  (매핑된 자료형 역시 정확성을 보장할 수 없음)
"""


# 주문 내역 API response 의 json 포맷
ABLY_ORDER_HISTORY_SCRAPING_RESPONSE_JSON_FORMAT = {
    "per_page": int,
    "total_count": int,
    "current_page": int,
    "max_page_number": int,
    "default_delivery_sno": int,
    "order_items": [
        {
            "sno": int,
            "order_sno": int,
            "ea": int,
            "app_type": int,
            "goods_prepare_started_at": str,
            "goods_sent_at": str,
            "delivery_completed_at": None,
            "purchase_confirmed_at": None,
            "balance_accounts_scheduled_at": None,
            "invoice": str,
            "delivery_sno": int,
            "delivery_sno_at_ordered": int,
            "status": str,
            "option_info": str,
            "is_notified_delay_guide": bool,
            "is_pended": bool,
            "delivery_type": str,
            "is_today_combine_delivery": bool,
            "delivery_expected_info": {
                "start_date": str,
                "end_date": str,
                "lead_days": None,
                "date_type": int,
                "delivery_date_range": str,
                "postfix_description": None,
            },
            "processing_sub_status": int,
            "is_delayed_cancel": bool,
            "ordered_at": str,
            "checked_at": str,
            "buyer_name": str,
            "buyer_tel": str,
            "buyer_email": str,
            "goods_sno": int,
            "goods_name": str,
            "goods_custom_code": str,
            "pay_method_name": str,
            "delay_days": int,
            "is_delayed": bool,
            "delivery": {
                "sno": int,
                "name": str,
                "sweet_tracker_code": str,
            },
            "receiver_name": str,
            "receiver_tel": str,
            "receiver_addr": str,
            "receiver_postcode": str,
            "memo": str,
            "price": int,
            "delay_notified_at": None,
            "is_required_invoice": bool,
            "delivery_at_ordered": {
                "sno": int,
                "name": str,
                "sweet_tracker_code": str,
            },
            "custom_number": bool,
            "is_option_displayed": bool,
            "is_malignant_delayed": bool,
            "is_option_buyable": bool,
            "exact_coupon_discount": int,
            "exact_emoney_discount": int,
            "exact_amount": int,
            "coupon_amount_for_ably": int,
            "emoney_amount_for_ably": int,
        }
    ]
}
