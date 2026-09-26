"""
config_schema.py
----------------
기본 스키마 정의 모듈

Section-based configuration 기반 기본 설정 구조를 초기화하며,
각 플랫폼별 스키마, 기본 설정값, 메타 정보를 정의 및 반환

모든 스키마 구조와 기본 설정값, 메타 정보는 해당 메서드에서 정의되며, (Single Source Of Truth)
config_schema.yml 파일은 해당 메서드의 결과값을 단순 dump 한 것으로
추가적인 외부 수정이 아닐 시, 스키마 수정은 .yml 이 아닌 해당 코드의 직접 수정을 권고
"""


from config.constant.data_types import DataType
from config.constant.name_constants import (
    COMMON_SECTION_KEY,
    ABLY_SECTION_KEY,
    COUPANG_SECTION_KEY,
    VREVIEW_SECTION_KEY,
)
from config.constant.path_constants import CONFIG_SCHEMA_YML_PATH, SCHEMA_CONSTANTS_PY_PATH
from core.config.model.config_base_section_option import Section, Option, OptionMeta


def get_default_schema() -> dict[str, Section]:
    """
    기본 스키마 생성 함수

    Section-based configuration 구조 기반으로 플랫폼별 설정값을 정의 (Section/Option/OptionMeta)

    스키마 작성 방법 및 변수별 규칙은
    config_base_section_option.py 모듈 OptionMeta, Option 클래스의 docstring 확인 권고

    :return: Section 명이 최상위 key 가 되는 dict[str, Section]
    """

    schema = {}

    # ===================================================
    #  common
    # ===================================================

    common_section = Section(COMMON_SECTION_KEY)
    schema[COMMON_SECTION_KEY] = common_section

    common_section.add_option(
        Option(
            key='shopping_mall_name',
            value=None,
            meta=OptionMeta(
                is_required=False,
                default_value=None,
                data_type=DataType.STR,
                description='수집 요청 회사명'
            )
        )
    )
    common_section.add_option(
        Option(
            key='export_id',
            value='vreview',
            meta=OptionMeta(
                is_required=True,
                default_value=None,
                data_type=DataType.STR,
                description='export 식별 id 값',
            )
        )
    )
    common_section.add_option(
        Option(
            key='start_date',
            value=None,
            meta=OptionMeta(
                is_required=True,
                default_value='2019-10-01',
                data_type=DataType.DATE,
                description='API 수집 시작 날짜',
            ),
        )
    )
    common_section.add_option(
        Option(
            key='start_time',
            value='00:00:00',
            meta=OptionMeta(
                is_required=True,
                default_value='00:00:00',
                data_type=DataType.TIME,
                description='API 수집 시작 시간',
            ),
        )
    )
    common_section.add_option(
        Option(
            key='end_date',
            value=None,
            meta=OptionMeta(
                is_required=True,
                default_value=None,
                data_type=DataType.DATE,
                description='API 수집 끝 날짜',
            ),
        )
    )
    common_section.add_option(
        Option(
            key='end_time',
            value=None,
            meta=OptionMeta(
                is_required=True,
                default_value='23:59:59',
                data_type=DataType.TIME,
                description='API 수집 끝 시간',
            ),
        )
    )

    # ===================================================
    #  ably
    # ===================================================

    ably_section = Section(ABLY_SECTION_KEY)
    schema[ABLY_SECTION_KEY] = ably_section

    ably_section.add_option(
        Option(
            key='token',
            value=None,
            meta=OptionMeta(
                is_required=True,
                default_value=None,
                data_type=DataType.STR,
                description='ably 회원 토큰 전문 (Authentication Scheme + Access Token)',
            ),
        )
    )
    ably_section.add_option(
        Option(
            key='review_scraping_per_page',
            value=500,
            meta=OptionMeta(
                is_required=True,
                default_value=500,
                data_type=DataType.UNSIGNED_INT,
                description='ably 리뷰 API 요청 시 한 번에 응답 받을 데이터 개수',
            ),
        )
    )
    ably_section.add_option(
        Option(
            key='order_history_scraping_per_page',
            value=50,
            meta=OptionMeta(
                is_required=True,
                default_value=50,
                data_type=DataType.UNSIGNED_INT,
                description='ably 주문 내역 API 요청 시 한 번에 응답 받을 데이터 개수',
            ),
        )
    )

    # ===================================================
    #  coupang
    # ===================================================

    coupang_section = Section(COUPANG_SECTION_KEY)
    schema[COUPANG_SECTION_KEY] = coupang_section

    coupang_section.add_option(
        Option(
            key='cookie',
            value=None,
            meta=OptionMeta(
                is_required=True,
                default_value=None,
                data_type=DataType.STR,
                description='coupang 회원 토큰 전문 (cookie)'
            ),
        )
    )
    coupang_section.add_option(
        Option(
            key='review_scraping_per_page',
            value=500,
            meta=OptionMeta(
                is_required=True,
                default_value=500,
                data_type=DataType.UNSIGNED_INT,
                description='coupang 리뷰 API 요청 시 한 번에 응답 받을 데이터 개수',
            ),
        )
    )

    # ===================================================
    #  vreview
    # ===================================================

    vreview_section = Section(VREVIEW_SECTION_KEY)
    schema[VREVIEW_SECTION_KEY] = vreview_section

    vreview_section.add_option(
        Option(
            key='shopping_mall_id',
            value=None,
            meta=OptionMeta(
                is_required=True,
                default_value=None,
                data_type=DataType.UNSIGNED_INT,
                description='vreview 에 등록된 쇼핑몰 id'
            ),
        )
    )
    vreview_section.add_option(
        Option(
            key='token',
            value=None,
            meta=OptionMeta(
                is_required=True,
                default_value=None,
                data_type=DataType.STR,
                description='vreview 회원 토큰 전문 (Authentication Scheme + Access Token)'
            ),
        )
    )
    vreview_section.add_option(
        Option(
            key='review_scraping_per_page',
            value=500,
            meta=OptionMeta(
                is_required=True,
                default_value=500,
                data_type=DataType.UNSIGNED_INT,
                description='vreview 리뷰 API 요청 시 한 번에 응답 받을 데이터 개수',
            ),
        )
    )
    vreview_section.add_option(
        Option(
            key='product_id',
            value=None,
            meta=OptionMeta(
                is_required=False,
                default_value=None,
                data_type=DataType.UNSIGNED_INT,
                description='vreview 리뷰 API 요청 시 타겟 상품 id',
            ),
        )
    )
    vreview_section.add_option(
        Option(
            key='review_group_id',
            value=None,
            meta=OptionMeta(
                is_required=False,
                default_value=None,
                data_type=DataType.UNSIGNED_INT,
                description='vreview 리뷰 API 요청 시 타겟 상품 그룹 id',
            ),
        )
    )
    vreview_section.add_option(
        Option(
            key='split_chunk_size',
            value=500,
            meta=OptionMeta(
                is_required=True,
                default_value=500,
                data_type=DataType.UNSIGNED_INT,
                description='수집된 리뷰를 vreview 이관용 개별 엑셀 파일에 나눠 담을 개수 단위 (반드시 500 이하)',
            ),
        )
    )
    vreview_section.add_option(
        Option(
            key='hide_batch_size',
            value=100,
            meta=OptionMeta(
                is_required=True,
                default_value=100,
                data_type=DataType.UNSIGNED_INT,
                description='vreview 리뷰 숨김 API 요청 시 한 번에 요청할 데이터 개수',
            ),
        )
    )

    return schema


# 스키마 수정 후엔 반드시 한 번씩 해당 모듈을 실행해주세요
if __name__ == "__main__":
    
    # 순환 참조 방지
    from core.common.bootstrap.config_schema_initialize import initialize_config_schema

    initialize_config_schema(CONFIG_SCHEMA_YML_PATH, SCHEMA_CONSTANTS_PY_PATH)
