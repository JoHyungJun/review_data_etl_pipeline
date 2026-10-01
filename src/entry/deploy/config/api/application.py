"""
application.py
--------------

FastAPI 객체 생성 및 개별 router, error handler 조립 모듈
"""


from fastapi import FastAPI

from entry.deploy.config.api.error_handler import external_scraping_api_authentication_expired_error_handler, \
    value_error_handler, default_error_handler
from entry.deploy.config.api.router.pipeline import pipeline_router
from error.api import ExternalScrapingApiAuthenticationExpiredError


# FastAPI 객체 생성
application = FastAPI()


# router
application.include_router(pipeline_router)


# error handler
application.add_exception_handler(
    ExternalScrapingApiAuthenticationExpiredError,
    external_scraping_api_authentication_expired_error_handler,
)

application.add_exception_handler(
    ValueError,
    value_error_handler,
)

application.add_exception_handler(
    Exception,
    default_error_handler,
)
