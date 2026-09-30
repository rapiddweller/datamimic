import json
from argparse import Namespace
from decimal import Decimal
from pathlib import Path
from typing import Literal

from datamimic_ce.engine.dsl.parsers.document.descriptor_parser import DescriptorParser
from datamimic_ce.engine.dsl.statements.setup.setup_statement import SetupStatement
from datamimic_ce.engine.runtime import api as runtime_api
from datamimic_ce.engine.runtime.contracts import (
    FactoryConfig,
    PlatformConfiguration,
    PlatformProperties,
    RunRequest,
    RunResult,
    RunSession,
)
from datamimic_ce.engine.runtime.lifecycle import runner
from datamimic_ce.engine.runtime.lifecycle.config import get_settings
from datamimic_ce.interfaces.cli import runtime as cli_runtime
from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest
from datamimic_ce.interfaces.python.datamimic import DataMimic
from datamimic_ce.interfaces.python.factory import DataMimicTestFactory


def test_runtime_run_capture_contract_permission_is_exact() -> None:
    contract_path = Path(__file__).resolve().parents[3] / "architecture-contract.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    rule = next(rule for rule in contract["rules"] if rule["id"] == "RUNTIME-API-TYPES")
    allowed_positions = rule["allowed_positions"]
    qualified_name = "datamimic_ce.engine.runtime.api.run"
    capture_positions = [
        (entry["position"], entry["field_path"], entry["annotation"])
        for entry in allowed_positions
        if entry["qualified_name"] == qualified_name
    ]

    assert len(capture_positions) == 3
    assert set(capture_positions) == {
        ("return", "captured", "dict[str, list[dict[str, object]]]"),
        ("return", "captured", "dict[str, object]"),
        ("return", "captured", "object"),
    }
    assert all("*" not in entry["qualified_name"] for entry in allowed_positions)
    assert all("*" not in entry["field_path"] for entry in allowed_positions)


class SessionStub:
    def __init__(self, captured: dict[str, list[dict[str, object]]] | None = None) -> None:
        self.executed = False
        self.captured = captured if captured is not None else {"entity": [{"id": 1}]}

    def execute(self) -> RunResult:
        self.executed = True
        return RunResult(self.captured)

    def capture_test_result(self) -> dict[str, list[dict[str, object]]] | None:
        return self.captured


def test_runtime_session_exposes_live_native_capture_before_and_after_execution(tmp_path: Path) -> None:
    descriptor = tmp_path / "descriptor.xml"
    descriptor.write_text("<setup />", encoding="utf-8")
    session = runner.create_run_session(RunRequest(descriptor_path=descriptor, test_mode=True))

    captured_before = session.capture_test_result()

    assert type(captured_before) is dict
    assert captured_before == {}
    result = session.execute()
    assert result.captured is captured_before
    assert session.capture_test_result() is captured_before


def test_runtime_session_captures_named_empty_product(tmp_path: Path) -> None:
    descriptor = tmp_path / "descriptor.xml"
    descriptor.write_text(
        '<setup rngSeed="1"><generate name="empty" count="0"><key name="id" constant="1"/></generate></setup>',
        encoding="utf-8",
    )
    session = runner.create_run_session(RunRequest(descriptor_path=descriptor, test_mode=True))
    captured = session.capture_test_result()

    assert type(captured) is dict
    assert captured == {}
    assert session.execute().captured is captured
    assert captured == {"empty": []}
    assert session.capture_test_result() is captured


def test_runtime_session_accumulates_repeat_execution_without_replacing_prior_rows(tmp_path: Path) -> None:
    descriptor = tmp_path / "descriptor.xml"
    descriptor.write_text(
        '<setup rngSeed="1"><generate name="rows" count="1">'
        '<key name="id" generator="IncrementGenerator"/></generate></setup>',
        encoding="utf-8",
    )
    session = runner.create_run_session(RunRequest(descriptor_path=descriptor, test_mode=True))

    first = session.execute().captured
    assert type(first) is dict
    first_row = first["rows"][0]

    second = session.execute().captured

    assert second is first
    assert len(second["rows"]) == 2
    assert second["rows"][0] is first_row


def test_runtime_session_preserves_native_row_and_leaf_identity(tmp_path: Path) -> None:
    descriptor = tmp_path / "descriptor.xml"
    descriptor.write_text(
        '<setup rngSeed="1"><generate name="rows" count="1">'
        '<key name="id" constant="1"/>'
        '<key name="amount" type="decimal" min="1" max="1"/>'
        '<nestedKey name="details" type="dict"><key name="label" constant="native"/></nestedKey>'
        '<nestedKey name="items" type="list" count="1"><key name="value" constant="leaf"/></nestedKey>'
        "</generate></setup>",
        encoding="utf-8",
    )
    session = runner.create_run_session(RunRequest(descriptor_path=descriptor, test_mode=True))

    captured = session.execute().captured
    assert type(captured) is dict
    row = captured["rows"][0]
    details = row["details"]
    items = row["items"]
    amount = row["amount"]
    assert isinstance(amount, Decimal)

    details["label"] = "mutated"
    items[0]["value"] = "mutated"
    again = session.capture_test_result()

    assert again is captured
    assert again["rows"][0] is row
    assert again["rows"][0]["details"] is details
    assert again["rows"][0]["items"] is items
    assert again["rows"][0]["amount"] is amount
    assert again["rows"][0]["details"]["label"] == "mutated"
    assert again["rows"][0]["items"][0]["value"] == "mutated"


def test_runtime_session_keeps_capture_disabled_outside_test_mode(tmp_path: Path) -> None:
    descriptor = tmp_path / "descriptor.xml"
    descriptor.write_text("<setup />", encoding="utf-8")
    session = runner.create_run_session(RunRequest(descriptor_path=descriptor))

    assert session.execute().captured is None
    try:
        session.capture_test_result()
    except ValueError as error:
        assert str(error) == "Cannot capture test result in non-test mode"
    else:
        raise AssertionError("runtime capture must fail outside test mode")


def test_factory_single_and_batch_keep_capture_identity_and_custom_data_mutable(tmp_path: Path, monkeypatch) -> None:
    descriptor = tmp_path / "descriptor.xml"
    descriptor.write_text(
        '<setup rngSeed="1"><generate name="entity" count="1">'
        '<key name="id" generator="IncrementGenerator"/></generate></setup>',
        encoding="utf-8",
    )
    sessions: list[RunSession] = []

    def create_session(request: RunRequest) -> RunSession:
        session = runner.create_run_session(request)
        sessions.append(session)
        return session

    monkeypatch.setattr("datamimic_ce.interfaces.python.factory.create_run_session", create_session)
    factory = DataMimicTestFactory(descriptor, "entity")
    custom_data = {"metadata": {"labels": []}}

    entity = factory.create(custom_data)
    single_capture = sessions[-1].capture_test_result()
    assert entity is single_capture["entity"][0]
    assert entity["metadata"] is custom_data["metadata"]
    entity["metadata"]["labels"].append("single")
    assert custom_data["metadata"]["labels"] == ["single"]

    batch = factory.create_batch(2, custom_data)
    batch_capture = sessions[-1].capture_test_result()
    assert batch is batch_capture["entity"]
    assert all(row is captured for row, captured in zip(batch, batch_capture["entity"], strict=True))
    assert len(batch) == 2
    assert all(row["metadata"] is custom_data["metadata"] for row in batch)
    batch[0]["metadata"]["labels"].append("batch")
    assert batch[1]["metadata"]["labels"] == ["single", "batch"]


def test_data_mimic_test_returns_native_capture(monkeypatch) -> None:
    result = {"entity": [{"id": 1}]}
    session = SessionStub(result)
    monkeypatch.setattr("datamimic_ce.interfaces.python.data_mimic_test.create_run_session", lambda _request: session)
    test_engine = DataMimicTest(Path("."), "descriptor.xml", capture_test_result=True)

    assert test_engine.capture_result() is result


def test_python_api_uses_runtime_request_and_preserves_factory_config(monkeypatch) -> None:
    captured: list[RunRequest] = []
    result = {"entity": [{"id": 1}]}
    session = SessionStub(result)

    def create_run_session(request: RunRequest) -> RunSession:
        captured.append(request)
        return session

    monkeypatch.setattr("datamimic_ce.interfaces.python.datamimic.create_run_session", create_run_session)

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
    monkeypatch.setattr("datamimic_ce.interfaces.python.data_mimic_test.create_run_session", lambda _request: session)
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
        *,
        profile_loader: object,
    ) -> SetupStatement:
        seen_environments.append(environment)
        return original_parse(path, properties, environment, profile_loader=profile_loader)

    class SetupTaskStub:
        def __init__(self, **_kwargs: object) -> None:
            pass

        def execute(self) -> None:
            pass

    monkeypatch.setattr(get_settings(), "RUNTIME_ENVIRONMENT", "development")
    monkeypatch.setattr(runner.DescriptorParser, "parse", parse_descriptor)
    monkeypatch.setattr(runner, "SetupTask", SetupTaskStub)
    session = runner.create_run_session(RunRequest(descriptor_path=descriptor, test_mode=True))

    assert session.execute().captured == {}
    assert seen_environments == ["development"]


def test_load_descriptor_properties_reads_found_file_and_defaults_when_missing(tmp_path: Path) -> None:
    descriptor = tmp_path / "model.xml"
    properties_file = tmp_path / "conf" / "environment.env.properties"
    properties_file.parent.mkdir()
    properties_file.write_text("# ignored\nuser = alice\nurl=https://example.test?a=b\n", encoding="utf-8")

    assert runtime_api.load_descriptor_properties(descriptor).root == {
        "user": "alice",
        "url": "https://example.test?a=b",
    }
    assert runtime_api.load_descriptor_properties(tmp_path / "missing" / "model.xml").root == {}


def test_load_descriptor_properties_preserves_parser_dictionary_identity(tmp_path: Path, monkeypatch) -> None:
    descriptor = tmp_path / "model.xml"
    properties: dict[str, str] = {"key": "value"}
    paths: list[Path] = []

    def parse(path: Path) -> dict[str, str]:
        paths.append(path)
        return properties

    monkeypatch.setattr(runtime_api, "parse_properties", parse)

    result = runtime_api.load_descriptor_properties(descriptor)

    assert result.root is properties
    assert paths == [tmp_path / "conf" / "environment.env.properties"]


def test_cli_passes_descriptor_properties_through_runtime_adapter(tmp_path: Path, monkeypatch) -> None:
    descriptor = tmp_path / "model.xml"
    descriptor.write_text("<setup />", encoding="utf-8")
    properties_file = tmp_path / "conf" / "environment.env.properties"
    properties_file.parent.mkdir()
    properties_file.write_text("tenant = demo\n", encoding="utf-8")
    requests: list[RunRequest] = []
    monkeypatch.setattr(cli_runtime, "run", requests.append)

    cli_runtime.execute_descriptor(descriptor, '{"mode":"test"}', "task", True)

    assert len(requests) == 1
    assert requests[0].descriptor_path == descriptor.resolve()
    assert requests[0].platform_props is not None
    assert requests[0].platform_props.root == {"tenant": "demo"}
    assert requests[0].platform_configs is not None
    assert requests[0].platform_configs.root == {"mode": "test"}
