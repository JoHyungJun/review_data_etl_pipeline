from types import SimpleNamespace

from pydantic import BaseModel

import entry.deploy.config.api.adapter.api_config_adapter as adapter_module
from core.config.constant.schema_constants import COMMON


class FakeOption:
    def __init__(self, key, value):
        self.key = key
        self.value = value


class FakeSection:
    def __init__(self, key):
        self.key = key
        self.options = []

    def add_option(self, option):
        self.options.append(option)


class FakeRequest:
    model_fields = {
        "common_config": None,
        "configs": None,
        "extra_config": None,
        "ignored_value": None,
    }

    def __init__(self, common_config, configs, extra_config, ignored_value):
        self.common_config = common_config
        self.configs = configs
        self.extra_config = extra_config
        self.ignored_value = ignored_value


class ExtraConfig(BaseModel):
    retries: int
    description: str | None


def setup_adapter(monkeypatch):
    monkeypatch.setattr(adapter_module, "Section", FakeSection)
    monkeypatch.setattr(adapter_module, "Option", FakeOption)


def options_as_dict(section):
    return {
        option.key: option.value
        for option in section.options
    }


def test_load_to_section_based_dict_converts_common_and_configs(monkeypatch):
    # Arrange
    setup_adapter(monkeypatch)

    request = FakeRequest(
        common_config=SimpleNamespace(
            model_dump=lambda: {
                "shopping_mall_name": "test_mall",
                "start_date": "2026-01-01",
                "optional_value": None,
            }
        ),
        configs={
            "SCRAPER": {
                "enabled": True,
                "retry_count": 3,
                "optional_value": None,
            }
        },
        extra_config={},
        ignored_value="not a dict",
    )

    # Act
    result = adapter_module.ApiConfigAdapter.load_to_section_based_dict(request)

    # Assert
    assert set(result) == {COMMON.SECTION_KEY, "SCRAPER", "extra_config"}

    assert options_as_dict(result[COMMON.SECTION_KEY]) == {
        "shopping_mall_name": "test_mall",
        "start_date": "2026-01-01",
        "optional_value": None,
    }

    assert options_as_dict(result["SCRAPER"]) == {
        "enabled": "True",
        "retry_count": "3",
        "optional_value": None,
    }

    assert "extra_config" in result
    assert "ignored_value" not in result


def test_load_to_section_based_dict_converts_extra_basemodel_to_section(
    monkeypatch,
):
    # Arrange
    setup_adapter(monkeypatch)

    request = FakeRequest(
        common_config=SimpleNamespace(
            model_dump=lambda: {"shopping_mall_name": "test_mall"}
        ),
        configs={},
        extra_config=ExtraConfig(
            retries=3,
            description=None,
        ),
        ignored_value=123,
    )

    # Act
    result = adapter_module.ApiConfigAdapter.load_to_section_based_dict(request)

    # Assert
    assert options_as_dict(result["extra_config"]) == {
        "retries": "3",
        "description": None,
    }


def test_load_to_section_based_dict_ignores_common_section_collision(
    monkeypatch,
):
    setup_adapter(monkeypatch)

    request = FakeRequest(
        common_config=SimpleNamespace(
            model_dump=lambda: {"shopping_mall_name": "test_mall"}
        ),
        configs={
            COMMON.SECTION_KEY: {
                "shopping_mall_name": "overridden_mall"
            }
        },
        extra_config={},
        ignored_value=None,
    )

    result = adapter_module.ApiConfigAdapter.load_to_section_based_dict(request)

    assert options_as_dict(result[COMMON.SECTION_KEY]) == {
        "shopping_mall_name": "test_mall"
    }
