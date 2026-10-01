"""
review_scraper_builder.py
-------------------------

로컬 환경용 리뷰 scrap API 관련 config 인스턴스의 빌더 모듈
"""


from core.config.constant.schema_constants import COMMON, ABLY, COUPANG, VREVIEW
from core.config.model.config_registry import ConfigRegistry
from domain.platform.ably.api.review_scraping_config import AblyReviewScrapingConfig
from domain.platform.coupang.api.review_scraping_config import CoupangReviewScrapingConfig
from domain.platform.vreview.api.review_scraping_config import VReviewReviewScrapingConfig


def build_ably_review_scraping_config(config_registry: ConfigRegistry) -> AblyReviewScrapingConfig:
    """
    A-bly 의 리뷰 scraping API 관련 config 인스턴스인 AblyReviewScrapingConfig 를 반환

    :param config_registry: 설정값이 담긴 인스턴스 ConfigRegistry
    :return: AblyReviewScrapingConfig 인스턴스
    """

    return AblyReviewScrapingConfig(
        start_date=config_registry.get_value(
            section_key=COMMON.SECTION_KEY,
            option_name=COMMON.START_DATE,
        ),
        start_time=config_registry.get_value(
            section_key=COMMON.SECTION_KEY,
            option_name=COMMON.START_TIME,
        ),
        end_date=config_registry.get_value(
            section_key=COMMON.SECTION_KEY,
            option_name=COMMON.END_DATE,
        ),
        end_time=config_registry.get_value(
            section_key=COMMON.SECTION_KEY,
            option_name=COMMON.END_TIME,
        ),

        token=config_registry.get_value(
            section_key=ABLY.SECTION_KEY,
            option_name=ABLY.TOKEN,
        ),
        per_page=config_registry.get_value(
            section_key=ABLY.SECTION_KEY,
            option_name=ABLY.REVIEW_SCRAPING_PER_PAGE,
        ),
    )


def build_coupang_review_scraping_config(config_registry: ConfigRegistry) -> CoupangReviewScrapingConfig:
    """
    Coupang 의 리뷰 scraping API 관련 config 인스턴스인 CoupangReviewScrapingConfig 를 반환

    :param config_registry: 설정값이 담긴 인스턴스 ConfigRegistry
    :return: CoupangReviewScrapingConfig 인스턴스
    """

    return CoupangReviewScrapingConfig(
        start_date=config_registry.get_value(
            section_key=COMMON.SECTION_KEY,
            option_name=COMMON.START_DATE,
        ),
        end_date=config_registry.get_value(
            section_key=COMMON.SECTION_KEY,
            option_name=COMMON.END_DATE,
        ),

        cookie=config_registry.get_value(
            section_key=COUPANG.SECTION_KEY,
            option_name=COUPANG.COOKIE,
        ),
        per_page=config_registry.get_value(
            section_key=COUPANG.SECTION_KEY,
            option_name=COUPANG.REVIEW_SCRAPING_PER_PAGE,
        ),
    )


def build_vreview_review_scraping_config(config_registry: ConfigRegistry) -> VReviewReviewScrapingConfig:
    """
    VReview 의 리뷰 scraping API 관련 config 인스턴스인 VReviewReviewScrapingConfig 를 반환

    :param config_registry: 설정값이 담긴 인스턴스 ConfigRegistry
    :return: VReviewReviewScrapingConfig 인스턴스
    """

    return VReviewReviewScrapingConfig(
        start_date=config_registry.get_value(
            section_key=COMMON.SECTION_KEY,
            option_name=COMMON.START_DATE,
        ),
        end_date=config_registry.get_value(
            section_key=COMMON.SECTION_KEY,
            option_name=COMMON.END_DATE,
        ),

        token=config_registry.get_value(
            section_key=VREVIEW.SECTION_KEY,
            option_name=VREVIEW.TOKEN,
        ),
        per_page=config_registry.get_value(
            section_key=VREVIEW.SECTION_KEY,
            option_name=VREVIEW.REVIEW_SCRAPING_PER_PAGE,
        ),
        product_id=config_registry.get_value(
            section_key=VREVIEW.SECTION_KEY,
            option_name=VREVIEW.PRODUCT_ID,
        ),
        review_group_id=config_registry.get_value(
            section_key=VREVIEW.SECTION_KEY,
            option_name=VREVIEW.REVIEW_GROUP_ID,
        ),
    )
