from unittest.mock import MagicMock, patch

from core.config.model.config_registry import ConfigRegistry
from entry.deploy.config.api.dto.base.base_api_request import BaseApiRequest
from factory.config.registry.deploy import build_deploy_api_config_registry


def test_build_deploy_api_config_registry():
    # Arrange
    request = MagicMock(spec=BaseApiRequest)
    parsed_api_data = {"COMMON": MagicMock()}
    expected_registry = MagicMock(spec=ConfigRegistry)

    with (
        patch(
            "factory.config.registry.deploy.ApiConfigAdapter.load_to_section_based_dict",
            return_value=parsed_api_data,
        ) as mock_adapter,
        patch(
            "factory.config.registry.deploy.ConfigRegistry",
            return_value=expected_registry,
        ) as mock_registry,
    ):
        # Act
        result = build_deploy_api_config_registry(request)

    # Assert
    mock_adapter.assert_called_once_with(request)
    mock_registry.assert_called_once_with(
        section_based_config_dict=parsed_api_data
    )
    assert result is expected_registry
