"""
review_scraping_format.py
-------------------------

A-bly review scraping API response 의 json 포맷 모듈

주의 사항
- RESPONSE_JSON_FORMAT 의 경우 response 로 전달되는 전체 json 포맷 및 자료형 매핑 데이터지만,
  스키마 참고용으로만 활용하고 해당 상수의 데이터를 직접 활용하지 않는 것을 권고
  (매핑된 자료형 역시 정확성을 보장할 수 없음)
"""


# 리뷰 API response 의 json 포맷
ABLY_REVIEW_SCRAPING_RESPONSE_JSON_FORMAT = {
    "reviews": [
        {
            "sno": int,
            "contents": str,
            "images": list,
            "status": int,
            "created_at": str,
            "updated_at": str,
            "goods": {
                "sno": int,
                "name": str,
                "image": str,
                "image_webp": str,
                "image_still": str,
                "sku_code": str,
                "is_open": bool,
                "thumbnail_ratio_with_one_point_two": str,
                "thumbnail_webp_ratio_with_one_point_two": str,
                "is_overseas_delivery": bool
            },
            "size": str,
            "height": str,
            "satisfaction": bool,
            "order_item_sno": int
        }
    ],
    "total_count": int
}
