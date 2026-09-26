"""
review_scraping_format.py
-------------------------

VReview review scraping API response 의 json 포맷 모듈

주의 사항
- RESPONSE_JSON_FORMAT 의 경우 response 로 전달되는 전체 json 포맷 및 자료형 매핑 데이터지만,
  스키마 참고용으로만 활용하고 해당 상수의 데이터를 직접 활용하지 않는 것을 권고
  (매핑된 자료형 역시 정확성을 보장할 수 없음)
"""


# 리뷰 API response 의 json 포맷
VREVIEW_REVIEW_SCRAPING_RESPONSE_JSON_FORMAT = {
    "count": int,
    "next": str,
    "previous": str,
    "results": [
        {
            "id": int,
            "author_name": str,
            "text": str,
            "rating": int,
            "main_content_type": str,
            "is_visible": bool,
            "helpful_count": int,
            "report_status": str,
            "report_counts": int,
            "edited_at": str,
            "created_at": str,
            "product": {
                "id": int,
                "name": str,
                "remote_id": str,
                "url": str
            },
            "review_group": {
                "id": int,
                "name": str,
            },
            "order": str,
            "comments": list,
            "thumbnail_content": {
                "type": str,
                "data": str
            },
            "thumbnail_contents": [
                {
                    "type": str,
                    "data": str
                }
            ],
            "upload_from": str,
            "origin_from": str,
            "user_nickname": str,
            "questions": [
                {
                    "question_type": str,
                    "question": str,
                    "answer": str,
                    "answer_type": str
                }
            ],
            "fixed": {
                "products": list,
                "review_groups": list
            },
            "sequence": str,
            "reward": {
                "link": str,
                "unrewardable_reason": str,
                "requests": [
                    {
                        "status": str,
                        "reason": str,
                        "amount": int,
                        "review_category": str,
                        "updated_at": str,
                        "is_manual": bool,
                        "approved_at": str,
                        "created_at": str
                    }
                ],
                "satisfied_rule_groups": list,
                "is_rewardable": bool
            },
            "text_sentiment_score": str,
            "sentiment_score": str,
            "review_hash_id": str,
            "review_type": str,
            "topics": list,
            "labels": list,
            "selected_options": [
                {
                    "name": str,
                    "value": str
                }
            ]
        },
    ]
}
