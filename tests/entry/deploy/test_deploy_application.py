from pathlib import Path
from unittest.mock import Mock

import pytest

import entry.deploy.deploy_application as deploy_module
from core.common.bootstrap import run_bootstrap
from entry.deploy.deploy_application import DeployApplication
from util.runtime_environment_util import resolve_value_from_environment_variables


def test_init_builds_bootstrap_config_from_environment(monkeypatch):
    # Arrange
    TEST_SENTIMENT_MODEL_PATH = "/tmp/model"
    TEST_APPLICATION_LOG_PATH = "/tmp/application.log"
    TEST_SENTIMENT_EVENT_LOG_PATH = "/tmp/sentiment.jsonl"
    TEST_SENTIMENT_CONFIG_TUNER_STATISTICS_META_LOG_PATH = "/tmp/statistics.jsonl"

    environment_values = {
        "SENTIMENT_MODEL_PATH":TEST_SENTIMENT_MODEL_PATH,
        "APPLICATION_LOG_PATH": TEST_APPLICATION_LOG_PATH,
        "SENTIMENT_EVENT_LOG_PATH": TEST_SENTIMENT_EVENT_LOG_PATH,
        "SENTIMENT_CONFIG_TUNER_STATISTICS_META_LOG_PATH": TEST_SENTIMENT_CONFIG_TUNER_STATISTICS_META_LOG_PATH,
    }

    monkeypatch.setattr(
        deploy_module,
        resolve_value_from_environment_variables.__name__,
        lambda key: environment_values[key],
    )

    # Act
    application = DeployApplication()

    # Assert
    config = application.bootstrap_config

    assert config.sentiment_model_path == Path(TEST_SENTIMENT_MODEL_PATH)
    assert config.application_log_path == Path(TEST_APPLICATION_LOG_PATH)
    assert config.sentiment_event_log_path == Path(TEST_SENTIMENT_EVENT_LOG_PATH)
    assert config.sentiment_config_tuner_statistics_meta_log_path == Path(TEST_SENTIMENT_CONFIG_TUNER_STATISTICS_META_LOG_PATH)
    assert config.schema_yaml_path == deploy_module.CONFIG_SCHEMA_YML_PATH
    assert config.schema_constants_py_path == deploy_module.SCHEMA_CONSTANTS_PY_PATH


def test_validate_environment_succeeds_when_src_directory_exists(
        monkeypatch,
        tmp_path,
):
    # Arrange
    (tmp_path / deploy_module.SRC_DIRECTORY_NAME).mkdir()

    monkeypatch.setattr(
        deploy_module,
        "BASE_DIRECTORY_PATH",
        tmp_path,
    )

    # Act / Assert
    DeployApplication._validate_environment()


def test_validate_environment_raises_when_src_directory_is_missing(
        monkeypatch,
        tmp_path,
):
    # Arrange
    monkeypatch.setattr(
        deploy_module,
        "BASE_DIRECTORY_PATH",
        tmp_path,
    )

    # Act / Assert
    with pytest.raises(RuntimeError, match="src"):
        DeployApplication._validate_environment()


def test_run_executes_validate_bootstrap_and_uvicorn_in_order(monkeypatch):
    # Arrange
    application = DeployApplication.__new__(DeployApplication)
    application.bootstrap_config = Mock()

    execution_order = []

    def validate():
        execution_order.append("validate")

    def bootstrap(config):
        execution_order.append("bootstrap")
        assert config is application.bootstrap_config

    def run_uvicorn(**kwargs):
        execution_order.append("uvicorn")
        assert kwargs["app"] is deploy_module.application
        assert kwargs["host"] == "0.0.0.0"
        assert kwargs["port"] == 8000

    monkeypatch.setattr(application, DeployApplication._validate_environment.__name__, validate)
    monkeypatch.setattr(deploy_module, run_bootstrap.__name__, bootstrap)
    monkeypatch.setattr(deploy_module.uvicorn, "run", run_uvicorn)

    # Act
    application.run()

    # Assert
    assert execution_order == ["validate", "bootstrap", "uvicorn"]


def test_run_stops_when_environment_validation_fails(monkeypatch):
    # Arrange
    application = DeployApplication.__new__(DeployApplication)
    application.bootstrap_config = Mock()

    bootstrap_mock = Mock()
    uvicorn_mock = Mock()

    def fail_validation():
        raise RuntimeError("Missing required directory")

    monkeypatch.setattr(
        application,
        DeployApplication._validate_environment.__name__,
        fail_validation,
    )
    monkeypatch.setattr(deploy_module, run_bootstrap.__name__, bootstrap_mock)
    monkeypatch.setattr(deploy_module.uvicorn, "run", uvicorn_mock)

    # Act / Assert
    with pytest.raises(RuntimeError, match="Missing required directory"):
        application.run()

    bootstrap_mock.assert_not_called()
    uvicorn_mock.assert_not_called()
