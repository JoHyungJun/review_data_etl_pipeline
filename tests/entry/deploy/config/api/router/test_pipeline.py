from datetime import date, time
from types import SimpleNamespace
from unittest.mock import Mock

import entry.deploy.config.api.router.pipeline as pipeline_module
from entry.deploy.config.api.dto.implementation.pipeline.pipeline_response import PipelineStatus
from error.config import ConfigNotAvailableError


def build_test_request():
    return SimpleNamespace(
        common_config=SimpleNamespace(
            shopping_mall_name="test_mall",
            export_id=SimpleNamespace(
                get_export_id=lambda: "test_export",
            ),
            start_date=date(2026, 1, 1),
            start_time=time(0, 0),
            end_date=date(2026, 1, 31),
            end_time=time(23, 59),
        ),
        configs={},
    )


def build_test_pipeline(platform_name, output_path):
    return SimpleNamespace(
        run_pipeline=Mock(),
        get_platform=lambda: SimpleNamespace(
            get_platform_eng_name=lambda: platform_name,
        ),
        get_final_output_path=lambda: output_path,
    )


def setup_pipeline_dependencies(monkeypatch, pipelines):
    config_registry = SimpleNamespace(
        get_value=Mock(return_value="test_export"),
    )
    export = object()

    monkeypatch.setattr(
        pipeline_module,
        "build_deploy_api_config_registry",
        lambda request: config_registry,
    )
    monkeypatch.setattr(
        pipeline_module,
        "Export",
        SimpleNamespace(from_id=lambda export_id: export),
    )
    monkeypatch.setattr(
        pipeline_module,
        "export_pipeline_builder",
        lambda export, config_registry, environment: pipelines,
    )

    return config_registry


def test_run_pipelines_returns_success_result(monkeypatch):
    # Arrange
    request = build_test_request()
    pipeline = build_test_pipeline("test_platform", "/tmp/output.xlsx")

    config_registry = setup_pipeline_dependencies(
        monkeypatch,
        [pipeline],
    )

    # Act
    response = pipeline_module.run_pipelines(request)

    # Assert
    config_registry.get_value.assert_called_once_with(
        section_key=pipeline_module.COMMON.SECTION_KEY,
        option_name=pipeline_module.COMMON.EXPORT_ID,
    )
    pipeline.run_pipeline.assert_called_once_with()

    assert response.message == "Pipeline request completed successfully"
    assert response.shopping_mall_name == "test_mall"
    assert response.export_id == "test_export"
    assert response.start_date == date(2026, 1, 1)
    assert response.start_time == time(0, 0)
    assert response.end_date == date(2026, 1, 31)
    assert response.end_time == time(23, 59)

    assert len(response.datas) == 1
    assert response.datas[0].platform == "test_platform"
    assert response.datas[0].status == PipelineStatus.SUCCESS
    assert response.datas[0].final_output_path == "/tmp/output.xlsx"


def test_run_pipelines_skips_unavailable_config_and_continues(
    monkeypatch,
):
    # Arrange
    request = build_test_request()

    skipped_pipeline = build_test_pipeline("platform_a", "/tmp/a.xlsx")
    successful_pipeline = build_test_pipeline("platform_b", "/tmp/b.xlsx")

    def raise_config_error():
        raise ConfigNotAvailableError("Required configuration is missing")

    skipped_pipeline.run_pipeline.side_effect = raise_config_error

    setup_pipeline_dependencies(
        monkeypatch,
        [skipped_pipeline, successful_pipeline],
    )

    # Act
    response = pipeline_module.run_pipelines(request)

    # Assert
    skipped_pipeline.run_pipeline.assert_called_once_with()
    successful_pipeline.run_pipeline.assert_called_once_with()

    assert len(response.datas) == 2

    assert response.datas[0].platform == "platform_a"
    assert response.datas[0].status == PipelineStatus.SKIPPED
    assert response.datas[0].message == (
        "Some required configuration is not available"
    )
    assert response.datas[0].final_output_path is None

    assert response.datas[1].platform == "platform_b"
    assert response.datas[1].status == PipelineStatus.SUCCESS
    assert response.datas[1].final_output_path == "/tmp/b.xlsx"
