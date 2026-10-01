"""
error_handler.py
----------------

FastAPI 환경 및 애플리케이션 실행에서 발생할 수 있는 예외를
공통 포맷의 HTTP API response 로 변환하는 global error handler 관련 함수 모음 모듈
"""


from fastapi import Request, status
from fastapi.responses import JSONResponse

from entry.deploy.config.api.dto.base.base_api_response import BaseFailedApiResponse
from error.api import ExternalScrapingApiAuthenticationExpiredError


def external_scraping_api_authentication_expired_error_handler(
    request: Request,
    e: ExternalScrapingApiAuthenticationExpiredError,
) -> JSONResponse:

    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=BaseFailedApiResponse(
            message=f"External scraping API authentication has expired - {str(e)}",
        ).model_dump(),
    )


def value_error_handler(
    request: Request,
    e: ValueError,
) -> JSONResponse:

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=BaseFailedApiResponse(
            message=f"Invalid external configuration value - {str(e)}",
        ).model_dump(),
    )


def default_error_handler(
    request: Request,
    e: Exception,
) -> JSONResponse:

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=BaseFailedApiResponse(
            message="Internal server error",
        ).model_dump(),
    )
