"""
order_history_scraping_builder.py
--------------------------------

로컬 환경용 주문 내역 scrap API 관련 config 인스턴스의 빌더 모듈
"""


from core.config.constant.schema_constants import ABLY, COMMON
from core.config.model.config_registry import ConfigRegistry
from domain.platform.ably.api.order_history_scraping_config import AblyOrderHistoryScrapingConfig


def build_ably_order_history_scraping_config(config_registry: ConfigRegistry) -> AblyOrderHistoryScrapingConfig:
    """
    A-bly 의 주문 내역 scraping API 관련 config 인스턴스인 AblyOrderHistoryScrapingConfig 를 반환

    :param config_registry: 설정값이 담긴 인스턴스 ConfigRegistry
    :return: AblyOrderHistoryScrapingConfig 인스턴스
    """

    return AblyOrderHistoryScrapingConfig(
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
                option_name=ABLY.ORDER_HISTORY_SCRAPING_PER_PAGE,
            ),
        )
