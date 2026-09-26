"""
schema_constants.py
-------------------

스키마 및 설정값 정의에 사용되는 Section, Option 이름에 대한 상수 모음 모듈

클래스명 및 해당 클래스의 하위 상수 SECTION_KEY 은 Section 명을 의미하며,
하위 상수명 및 상수값은 Option 의 key 명을 의미함

주의 사항
- 해당 모듈은 generate_constants_from_schema() 메서드를 통해 자동 생성되며,
  실제 스키마의 작성 기준 (truth of source) 은 src/core/config/model/config_schema.py 모듈이고,
  상수 모듈 작성 과정에서 정보가 변경될 수 있음을 주의

- 상수들은 코드 내에서 스키마 및 설정값 접근 시 하드코딩 및 오탈자 방지를 위해 활용되므로,
  해당 모듈의 직접 수정을 금지,
  스키마 변경 시에는 반드시 truth of source 수정 후 codegen 메서드 실행으로
  데이터간의 정합성을 맞추는 방법을 강력히 강제

- 외부 파일로 작성되는 설정값들은,
  반드시 이 상수 모듈에 정의된 key 명으로 Section/Option 명이 정의되어야 함
"""


class COMMON:
    SECTION_KEY = 'common'

    SHOPPING_MALL_NAME = 'shopping_mall_name'
    EXPORT_ID = 'export_id'
    START_DATE = 'start_date'
    START_TIME = 'start_time'
    END_DATE = 'end_date'
    END_TIME = 'end_time'


class ABLY:
    SECTION_KEY = 'ably'

    TOKEN = 'token'
    REVIEW_SCRAPING_PER_PAGE = 'review_scraping_per_page'
    ORDER_HISTORY_SCRAPING_PER_PAGE = 'order_history_scraping_per_page'


class COUPANG:
    SECTION_KEY = 'coupang'

    COOKIE = 'cookie'
    REVIEW_SCRAPING_PER_PAGE = 'review_scraping_per_page'


class VREVIEW:
    SECTION_KEY = 'vreview'

    SHOPPING_MALL_ID = 'shopping_mall_id'
    TOKEN = 'token'
    REVIEW_SCRAPING_PER_PAGE = 'review_scraping_per_page'
    PRODUCT_ID = 'product_id'
    REVIEW_GROUP_ID = 'review_group_id'
    SPLIT_CHUNK_SIZE = 'split_chunk_size'
    HIDE_BATCH_SIZE = 'hide_batch_size'

