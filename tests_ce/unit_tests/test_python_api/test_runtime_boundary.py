from argparse import Namespace
from pathlib import Path
from typing import Literal

from datamimic_ce.data_mimic_test import DataMimicTest
from datamimic_ce.datamimic import DataMimic
from datamimic_ce.engine.dsl.parsers.descriptor_parser import DescriptorParser
from datamimic_ce.engine.dsl.statements.setup_statement import SetupStatement
from datamimic_ce.engine.runtime import runner
from datamimic_ce.engine.runtime.config import settings
from datamimic_ce.engine.runtime.contracts import (
    CapturedProducts,
    PlatformConfiguration,
    PlatformProperties,
    RunRequest,
    RunResult,
    RunSession,
)
from datamimic_ce.factory.factory_config import FactoryConfig as LegacyFactoryConfig
from datamimic_ce.interfaces.contracts import FactoryConfig


class SessionStub:
    def __init__(self, captured: dict[str, list[dict[str, object]]] | None = None) -> None:
        self.executed = False
        self.captured = captured if captured is not None else {"entity": [{"id": 1}]}

    def execute(self) -> RunResult:
        self.executed = True
        return RunResult(CapturedProducts.model_construct(root=self.captured))

    def capture_test_result(self) -> CapturedProducts | None:
        return CapturedProducts.model_construct(root=self.captured)


def test_python_api_uses_interface_request_and_preserves_factory_config_identity(monkeypatch) -> None:
    assert LegacyFactoryConfig is FactoryConfig
    captured: list[RunRequest] = []
    result = {"entity": [{"id": 1}]}
    session = SessionStub(result)

    def create_run_session(request: RunRequest) -> RunSession:
        captured.append(request)
        return session

    monkeypatch.setattr("datamimic_ce.datamimic.create_run_session", create_run_session)

    def transformer(_statement) -> None:
        pass

    factory_config = FactoryConfig("entity", 1, {"id": 1})
    properties: dict[str, object] = {"key": 1}
    configuration = {"config": "value"}
    engine = DataMimic(
        Path("descriptor.xml"),
        task_id="task-1",
        platform_props=properties,
        platform_configs=configuration,
        test_mode=True,
        factory_config=factory_config,
        args=Namespace(log_level="DEBUG"),
        statement_transformer=transformer,
    )

    assert captured == [
        RunRequest(
            descriptor_path=Path("descriptor.xml"),
            task_id="task-1",
            platform_props=PlatformProperties.model_construct(root=properties),
            platform_configs=PlatformConfiguration.model_construct(root=configuration),
            test_mode=True,
            factory_config=factory_config,
            args=Namespace(log_level="DEBUG"),
            statement_transformer=transformer,
        )
    ]
    assert captured[0].platform_props is not None
    assert captured[0].platform_props.root is properties
    assert captured[0].platform_configs is not None
    assert captured[0].platform_configs.root is configuration
    assert engine.parse_and_execute() is None
    assert session.executed
    assert engine.capture_test_result() is result


def test_data_mimic_test_keeps_disabled_capture_error(monkeypatch) -> None:
    session = SessionStub()
    monkeypatch.setattr("datamimic_ce.data_mimic_test.create_run_session", lambda _request: session)
    test_engine = DataMimicTest(Path("."), "descriptor.xml")

    try:
        test_engine.capture_result()
    except ValueError as error:
        assert str(error) == "Capturing test result mode is currently disable"
    else:
        raise AssertionError("disabled capture must fail")


def test_runtime_session_uses_current_environment_for_parsing(tmp_path: Path, monkeypatch) -> None:
    descriptor = tmp_path / "descriptor.xml"
    descriptor.write_text("<setup />", encoding="utf-8")
    original_parse = DescriptorParser.parse
    seen_environments: list[str] = []

    def parse_descriptor(
        path: Path,
        properties: dict[str, str] | None,
        environment: Literal["development", "production"],
    ) -> SetupStatement:
        seen_environments.append(environment)
        return original_parse(path, properties, environment)

    class SetupTaskStub:
        def __init__(self, **_kwargs: object) -> None:
            pass

        def execute(self) -> None:
            pass

    monkeypatch.setattr(settings, "RUNTIME_ENVIRONMENT", "development")
    monkeypatch.setattr(runner.DescriptorParser, "parse", parse_descriptor)
    monkeypatch.setattr(runner, "SetupTask", SetupTaskStub)
    session = runner.create_run_session(RunRequest(descriptor_path=descriptor, test_mode=True))

    assert session.execute().captured == CapturedProducts({})
    assert seen_environments == ["development"]
