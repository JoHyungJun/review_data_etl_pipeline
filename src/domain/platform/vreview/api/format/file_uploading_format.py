"""
review_scraping_format.py
-------------------------

VReview file uploading API response 의 json 포맷 모듈

주의 사항
- RESPONSE_JSON_FORMAT 의 경우 response 로 전달되는 전체 json 포맷 및 자료형 매핑 데이터지만,
  스키마 참고용으로만 활용하고 해당 상수의 데이터를 직접 활용하지 않는 것을 권고
  (매핑된 자료형 역시 정확성을 보장할 수 없음)
"""


VREVIEW_FILE_UPLOADING_RESPONSE_JSON_FORMAT = {
    "id": str,
    "preset": str,
    "created_at": str,
    "file_name": str,
    "status": str,
    "total_count": int,
}
