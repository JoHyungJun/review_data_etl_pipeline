import json

from fastapi import status

from entry.deploy.config.api.error_handler import (
    default_error_handler,
    external_scraping_api_authentication_expired_error_handler,
    value_error_handler,
)
from error.api import ExternalScrapingApiAuthenticationExpiredError


def get_response_json(response):
    return json.loads(response.body.decode("utf-8"))


def test_external_scraping_authentication_expired_returns_401():
    # Arrange
    error = ExternalScrapingApiAuthenticationExpiredError("token expired")

    # Act
    response = external_scraping_api_authentication_expired_error_handler(request=None, e=error)

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert get_response_json(response) == {
        "message": (
            "External scraping API authentication has expired - token expired"
        )
    }


def test_value_error_returns_400():
    # Arrange
    error = ValueError("invalid date")

    # Act
    response = value_error_handler(request=None, e=error)

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert get_response_json(response) == {
        "message": "Invalid external configuration value - invalid date"
    }


def test_default_error_returns_500_without_exposing_exception():
    # Arrange
    error = RuntimeError("internal database detail")

    # Act
    response = default_error_handler(request=None, e=error)

    # Assert
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert get_response_json(response) == {
        "message": "Internal server error"
    }
    assert "internal database detail" not in response.body.decode("utf-8")
