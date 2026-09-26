"""
review_scraping_format.py
-------------------------

Coupang review scraping API response 의 json 포맷 모듈

주의 사항
- RESPONSE_JSON_FORMAT 의 경우 response 로 전달되는 전체 json 포맷 및 자료형 매핑 데이터지만,
  스키마 참고용으로만 활용하고 해당 상수의 데이터를 직접 활용하지 않는 것을 권고
  (매핑된 자료형 역시 정확성을 보장할 수 없음)
"""


# 리뷰 API response 의 json 포맷
COUPANG_REVIEW_SCRAPING_RESPONSE_JSON_FORMAT = {
    "code": str,
    "message": str,
    "data": {
        "content": [
            {
                "reviewId": int,
                "productId": int,
                "itemName": str,
                "vendorItemId": int,
                "itemId": int,
                "vendorId": str,
                "reviewAt": int,
                "firstReviewAt": int,
                "modifiedAt": int,
                "rating": int,
                "memberName": str,
                "reviewTitle": str,
                "reviewContent": str,
                "memberSrl": int,
                "viSaleStatus": str,
                "deleted": bool,
                "blinded": bool,
                "emptyComment": bool,
                "createdAt": int,               # milli seconds time stamp
                "reviewSurveyAnswers": str,     # json array - json.loads(reviewSurveyAnswers) 으로 파싱 필요
                                                # [{
                                                #     "questions": str,
                                                #     "answer": str,
                                                #     "questionType": str,
                                                # }]

                "attachment": str,              # json array - json.loads(attachment) 으로 파싱 필요
                                                # "imageAttachments":
                                                #     [{
                                                #         "caption": str,
                                                #         "blinded": bool,
                                                #         "attachmentType": str,
                                                #         "uploadedFilePath": str,
                                                #         "thumbnailSrc": str,
                                                #         "imgSrc": str,
                                                #     }],
                                                # "videoAttachments": List[Dict]
                "eventId": int,                 # null
            },
        ],
        "pagination": {
            "currentPage": int,
            "totalPages": int,
            "totalElements": int,
            "countPerPage": int,
        }
    },
    "success": bool
}
