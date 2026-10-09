import json
import logging
from argparse import Namespace
from decimal import Decimal
from pathlib import Path
from typing import Literal, get_type_hints

import pytest

from datamimic_ce.engine.dsl.parsers.document.descriptor_parser import DescriptorParser
from datamimic_ce.engine.dsl.statements.setup.setup_statement import SetupStatement
from datamimic_ce.engine.io.exporters.diagnostics.test_result_exporter import TestResultExporter
from datamimic_ce.engine.runtime import api as runtime_api
from datamimic_ce.engine.runtime import contracts as runtime_contracts
from datamimic_ce.engine.runtime.contracts import (
    FactoryConfig,
    PlatformConfiguration,
    RunRequest,
    RunResult,
    RunSession,
)
from datamimic_ce.engine.runtime.lifecycle import runner
from datamimic_ce.engine.runtime.lifecycle.config import get_settings
from datamimic_ce.engine.runtime.lifecycle.runner import RuntimeRunSession
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
        if entry["qualified_name"] == qualified_name and entry["position"] == "return"
    ]

    assert len(capture_positions) == 3
    assert set(capture_positions) == {
        ("return", "captured", "dict[str, list[dict[str, object]]]"),
        ("return", "captured", "dict[str, object]"),
        ("return", "captured", "object"),
    }
    assert all("*" not in entry["qualified_name"] for entry in allowed_positions)
    assert all("*" not in entry["field_path"] for entry in allowed_positions)


def test_runtime_property_contract_permissions_are_exact() -> None:
    contract_path = Path(__file__).resolve().parents[3] / "architecture-contract.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    rule = next(rule for rule in contract["rules"] if rule["id"] == "RUNTIME-API-TYPES")
    allowed_positions = rule["allowed_positions"]
    property_positions = {
        (
            entry["qualified_name"],
            entry["position"],
            entry["field_path"],
            entry["annotation"],
        )
        for entry in allowed_positions
        if (
            entry["qualified_name"] == "datamimic_ce.engine.runtime.api.load_descriptor_properties"
            and entry["position"] == "return"
        )
        or (
            entry["qualified_name"]
            in {
                "datamimic_ce.engine.runtime.api.create_run_session",
                "datamimic_ce.engine.runtime.api.run",
            }
            and entry["position"] == "request"
            and entry.get("field_path") == "platform_props"
        )
    }

    assert property_positions == {
        (
            "datamimic_ce.engine.runtime.api.load_descriptor_properties",
            "return",
            "",
            "dict[str, str]",
        ),
        (
            "datamimic_ce.engine.runtime.api.create_run_session",
            "request",
            "platform_props",
            "dict[str, str]",
        ),
        (
            "datamimic_ce.engine.runtime.api.run",
            "request",
            "platform_props",
            "dict[str, str]",
        ),
    }
    assert all("*" not in entry["qualified_name"] for entry in allowed_positions)
    assert all("*" not in entry["field_path"] for entry in allowed_positions)


def test_runtime_scripting_state_permissions_are_exact() -> None:
    contract_path = Path(__file__).resolve().parents[3] / "architecture-contract.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    rule = next(rule for rule in contract["rules"] if rule["id"] == "RUNTIME-API-TYPES")
    allowed_positions = rule["allowed_positions"]
    permissions = [
        (
            entry["qualified_name"],
            entry["position"],
            entry["field_path"],
            entry["annotation"],
            entry.get("container_depth"),
        )
        for entry in allowed_positions
    ]
    api = "datamimic_ce.engine.runtime.api."
    map_permissions = {
        (api + name, position, "", annotation, depth)
        for name, position, annotation in (
            ("Context.evaluate_python_expression", "local_namespace", "dict[str, object] | None"),
            ("Context.scope_content", "return", "dict[str, object]"),
            ("Context.get_content_variables_products", "return", "dict[str, object]"),
            ("SetupContext.__init__", "namespace", "dict[str, object] | None"),
            ("SetupContext.__init__", "global_variables", "dict[str, object] | None"),
            ("SetupContext.namespace", "return", "dict[str, object]"),
            ("SetupContext.namespace", "value", "dict[str, object]"),
            ("SetupContext.global_variables", "return", "dict[str, object]"),
            ("SetupContext.eval_namespace", "return", "dict[str, object]"),
            ("SetupContext.__deepcopy__", "memo", "dict[int, object]"),
        )
        for depth in (None, 1)
    } | {
        (api + "Context.evaluate_python_expression", "return", "", "object", None),
        (api + "SetupContext.get_dynamic_class", "return", "", "object | None", None),
    }
    legacy_permissions = {
        (api + "run", "return", "captured", "dict[str, list[dict[str, object]]]", None),
        (api + "run", "return", "captured", "dict[str, object]", None),
        (api + "run", "return", "captured", "object", None),
        (api + "load_descriptor_properties", "return", "", "dict[str, str]", None),
        (api + "create_run_session", "request", "platform_props", "dict[str, str]", None),
        (api + "run", "request", "platform_props", "dict[str, str]", None),
        (api + "SetupContext.__init__", "clients", "", "dict[str, RegisteredClient] | None", None),
        (api + "SetupContext.clients", "return", "", "dict[str, RegisteredClient]", None),
        (api + "SetupContext.clients", "value", "", "dict[str, RegisteredClient]", None),
        (
            api + "SetupContext.__init__",
            "data_source_len",
            "",
            "dict[tuple[str | None, str | None], int] | None",
            None,
        ),
        (api + "SetupContext.data_source_len", "return", "", "dict[tuple[str | None, str | None], int]", None),
    }
    demographic_permissions = {
        (
            api + "SetupContext.__init__",
            "demographic_context",
            "overrides.transaction_profile",
            "Mapping[str, float]",
            None,
        ),
        (
            api + "SetupContext.demographic_context",
            "return",
            "overrides.transaction_profile",
            "Mapping[str, float]",
            None,
        ),
        (
            api + "SetupContext.set_demographic_context",
            "context",
            "overrides.transaction_profile",
            "Mapping[str, float]",
            None,
        ),
    }
    scripting_names = {permission[0] for permission in map_permissions}
    scripting_positions = {permission[1] for permission in map_permissions}
    scripting_permissions = [
        permission
        for permission in permissions
        if permission[0] in scripting_names and permission[1] in scripting_positions
    ]
    remaining_permissions = [
        permission
        for permission in permissions
        if permission not in scripting_permissions and permission not in demographic_permissions
    ]

    assert len(scripting_permissions) == 22
    assert set(scripting_permissions) == map_permissions
    assert len(permissions) == len(set(permissions)) == 36
    assert {
        permission for permission in permissions if permission in demographic_permissions
    } == demographic_permissions
    assert len(remaining_permissions) == 11
    assert set(remaining_permissions) == legacy_permissions
    assert all("*" not in permission[0] and "*" not in permission[2] for permission in permissions)


def test_runtime_properties_wrapper_is_removed() -> None:
    assert not hasattr(runtime_contracts, "PlatformProperties")


def test_runtime_property_loader_has_native_return_annotation() -> None:
    assert get_type_hints(runtime_api.load_descriptor_properties)["return"] == dict[str, str]


def test_run_request_has_native_property_map_annotation() -> None:
    assert get_type_hints(RunRequest)["platform_props"] == dict[str, str] | None


def test_run_request_has_integer_log_level_and_no_transport_args() -> None:
    assert get_type_hints(RunRequest)["log_level"] is int
    assert RunRequest.__dataclass_fields__["log_level"].default == logging.INFO
    assert "args" not in RunRequest.__dataclass_fields__


def test_capture_surfaces_annotate_native_rows_with_existing_optionality() -> None:
    expected_capture = dict[str, list[object]] | None

    assert get_type_hints(TestResultExporter.get_result)["return"] == dict[str, list[object]]
    assert get_type_hints(RunResult)["captured"] == expected_capture
    assert get_type_hints(RunSession.capture_test_result)["return"] == expected_capture
    assert get_type_hints(RuntimeRunSession.capture_test_result)["return"] == expected_capture
    assert get_type_hints(DataMimicTest.capture_result)["return"] == expected_capture
    assert get_type_hints(DataMimic.capture_test_result)["return"] == expected_capture


class SessionStub:
    def __init__(self, captured: dict[str, list[object]] | None = None) -> None:
        self.executed = False
        self.captured = captured if captured is not None else {"entity": [{"id": 1}]}

    def execute(self) -> RunResult:
        self.executed = True
        return RunResult(self.captured)

    def capture_test_result(self) -> dict[str, list[object]] | None:
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


def test_runtime_session_captures_explicit_and_lazy_scalar_rows_in_order(tmp_path: Path) -> None:
    explicit_descriptor = tmp_path / "explicit.xml"
    explicit_descriptor.write_text(
        '<setup rngSeed="7"><generate name="rows" count="2" target="TestResultExporter">'
        '<key name="#text" generator="IncrementGenerator"/></generate></setup>',
        encoding="utf-8",
    )
    explicit_session = runner.create_run_session(
        RunRequest(descriptor_path=explicit_descriptor, test_mode=True)
    )

    result = explicit_session.execute()
    explicit_capture = explicit_session.capture_test_result()
    explicit_rows = explicit_capture["rows"]

    assert result.captured is explicit_capture
    assert explicit_rows == [1, 2, {"#text": 1}, {"#text": 2}]
    assert explicit_session.capture_test_result()["rows"] is explicit_rows

    lazy_descriptor = tmp_path / "lazy.xml"
    lazy_descriptor.write_text(
        '<setup rngSeed="7"><generate name="rows" count="2">'
        '<key name="#text" generator="IncrementGenerator"/></generate></setup>',
        encoding="utf-8",
    )
    lazy_session = runner.create_run_session(RunRequest(descriptor_path=lazy_descriptor, test_mode=True))

    lazy_capture = lazy_session.execute().captured
    lazy_rows = lazy_capture["rows"]

    assert lazy_rows == [{"#text": 1}, {"#text": 2}]
    assert lazy_session.capture_test_result() is lazy_capture
    assert lazy_session.capture_test_result()["rows"] is lazy_rows


def test_runtime_session_keeps_nested_text_native_in_lazy_capture(tmp_path: Path) -> None:
    descriptor = tmp_path / "descriptor.xml"
    descriptor.write_text(
        '<setup rngSeed="7"><generate name="rows" count="1">'
        '<key name="id" constant="1"/>'
        '<nestedKey name="label" type="dict"><key name="#text" constant="inner"/></nestedKey>'
        "</generate></setup>",
        encoding="utf-8",
    )
    session = runner.create_run_session(RunRequest(descriptor_path=descriptor, test_mode=True))

    captured = session.execute().captured

    assert captured == {"rows": [{"id": "1", "label": {"#text": "inner"}}]}
    row = captured["rows"][0]
    label = row["label"]
    label["#text"] = "changed"
    again = session.capture_test_result()

    assert again is captured
    assert again["rows"][0] is row
    assert again["rows"][0]["label"] is label
    assert again["rows"][0]["label"]["#text"] == "changed"


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


@pytest.mark.parametrize("custom_data", [{"extra": True}, {}], ids=["populated", "empty"])
@pytest.mark.parametrize("method", ["create", "create_batch"], ids=["single", "batch"])
@pytest.mark.parametrize("row_kind", ["list", "scalar", "none", "update-capable"])
def test_factory_rejects_native_rows_only_when_overlay_is_supplied(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    custom_data: dict[str, object],
    method: str,
    row_kind: str,
) -> None:
    update_calls: list[dict[str, object]] = []

    class UpdateCapable:
        def update(self, _other: dict[str, object]) -> None:
            update_calls.append({"called": True})

    native_row: object = {
        "list": ["native", {"nested": []}],
        "scalar": "native",
        "none": None,
        "update-capable": UpdateCapable(),
    }[row_kind]
    session = SessionStub({"entity": [native_row]})
    monkeypatch.setattr("datamimic_ce.interfaces.python.factory.create_run_session", lambda _request: session)
    factory = DataMimicTestFactory(tmp_path / "unused.xml", "entity")

    if method == "create":
        assert factory.create() is native_row
        try:
            factory.create(custom_data)
        except Exception as error:
            observed_error = error
        else:
            observed_error = None
    else:
        batch = factory.create_batch(1)
        assert batch == [native_row]
        assert batch[0] is native_row
        try:
            factory.create_batch(1, custom_data)
        except Exception as error:
            observed_error = error
        else:
            observed_error = None
    assert update_calls == []
    assert type(observed_error) is TypeError
    assert str(observed_error) == "Factory custom_data requires dictionary rows"


def test_factory_overlay_preserves_dict_row_update_override_and_error(tmp_path: Path, monkeypatch) -> None:
    events: list[dict[str, object]] = []

    class Row(dict):
        def update(self, other) -> None:
            events.append(self)
            if other.get("fail"):
                raise RuntimeError("row update failed")
            super().update(other)

    row = Row(id=1)
    monkeypatch.setattr(
        "datamimic_ce.interfaces.python.factory.create_run_session",
        lambda _request: SessionStub({"entity": [row]}),
    )
    factory = DataMimicTestFactory(tmp_path / "unused.xml", "entity")

    assert factory.create({}) is row
    assert events == [row]
    with pytest.raises(RuntimeError, match="^row update failed$"):
        factory.create({"fail": True})
    assert events == [row, row]


def test_factory_batch_overlay_failure_keeps_prior_updates_and_stops_in_order(tmp_path: Path, monkeypatch) -> None:
    class Row(dict):
        def update(self, other) -> None:
            if self["id"] == 2:
                raise RuntimeError("second row failed")
            super().update(other)

    first, second, third = Row(id=1), Row(id=2), Row(id=3)
    session = SessionStub({"entity": [first, second, third]})
    monkeypatch.setattr("datamimic_ce.interfaces.python.factory.create_run_session", lambda _request: session)
    factory = DataMimicTestFactory(tmp_path / "unused.xml", "entity")

    with pytest.raises(RuntimeError, match="^second row failed$"):
        factory.create_batch(3, {"extra": True})

    assert first["extra"] is True
    assert "extra" not in second
    assert "extra" not in third


def test_factory_mixed_batch_overlay_is_sequential_and_keeps_partial_mutation(tmp_path: Path, monkeypatch) -> None:
    first = {"id": 1}
    native = ["not a mapping"]
    last = {"id": 3}
    session = SessionStub({"entity": [first, native, last]})
    monkeypatch.setattr("datamimic_ce.interfaces.python.factory.create_run_session", lambda _request: session)
    factory = DataMimicTestFactory(tmp_path / "unused.xml", "entity")

    with pytest.raises(TypeError, match="^Factory custom_data requires dictionary rows$"):
        factory.create_batch(3, {"extra": True})

    assert first == {"id": 1, "extra": True}
    assert "id" not in native
    assert last == {"id": 3}


def test_factory_empty_batch_accepts_empty_overlay(tmp_path: Path, monkeypatch) -> None:
    session = SessionStub({"entity": []})
    monkeypatch.setattr("datamimic_ce.interfaces.python.factory.create_run_session", lambda _request: session)
    factory = DataMimicTestFactory(tmp_path / "unused.xml", "entity")

    assert factory.create_batch(0, {}) == []


@pytest.mark.parametrize(
    ("captured", "count", "method"),
    [
        (None, 1, "create"),
        (None, 1, "create_batch"),
        ({"other": [{"id": 1}]}, 1, "create"),
        ({"other": [{"id": 1}]}, 1, "create_batch"),
        ({"entity": [["native"], ["extra"]]}, 2, "create"),
        ({"entity": [["native"]]}, 2, "create_batch"),
    ],
    ids=[
        "create-capture-disabled",
        "batch-capture-disabled",
        "create-entity-missing",
        "batch-entity-missing",
        "create-count-mismatch",
        "batch-count-mismatch",
    ],
)
def test_factory_capture_and_count_assertions_precede_overlay_guard(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    captured: dict[str, list[object]] | None,
    count: int,
    method: str,
) -> None:
    session = SessionStub()
    session.captured = captured
    monkeypatch.setattr("datamimic_ce.interfaces.python.factory.create_run_session", lambda _request: session)
    factory = DataMimicTestFactory(tmp_path / "unused.xml", "entity")

    with pytest.raises(AssertionError):
        if method == "create":
            factory.create({})
        else:
            factory.create_batch(count, {})


def test_factory_real_xml_target_capture_count_assertion_precedes_overlay(tmp_path: Path) -> None:
    descriptor = tmp_path / "descriptor.xml"
    descriptor.write_text(
        '<setup rngSeed="7"><generate name="entity" count="1" target="TestResultExporter">'
        '<key name="id" constant="1"/></generate></setup>',
        encoding="utf-8",
    )
    factory = DataMimicTestFactory(descriptor, "entity")

    with pytest.raises(AssertionError):
        factory.create({})


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

    assert captured[0].platform_props is properties
    assert captured == [
        RunRequest(
            descriptor_path=Path("descriptor.xml"),
            task_id="task-1",
            platform_props=properties,
            platform_configs=PlatformConfiguration.model_construct(root=configuration),
            test_mode=True,
            factory_config=factory_config,
            log_level=logging.DEBUG,
            statement_transformer=transformer,
        )
    ]
    assert captured[0].platform_configs is not None
    assert captured[0].platform_configs.root is configuration
    assert engine.parse_and_execute() is None
    assert session.executed
    assert engine.capture_test_result() is result


@pytest.mark.parametrize(
    ("args", "expected_level", "register_custom_level"),
    [
        (None, logging.INFO, False),
        (Namespace(), logging.INFO, False),
        (Namespace(log_level="unknown-level"), logging.INFO, False),
        (Namespace(log_level=17), logging.INFO, False),
        (Namespace(log_level="debug"), logging.DEBUG, False),
        (Namespace(log_level="notice"), 25, True),
    ],
    ids=["none", "missing", "unknown", "non-string", "lowercase", "custom"],
)
def test_python_api_resolves_transport_log_level_before_real_runtime(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    args: Namespace | None,
    expected_level: int,
    register_custom_level: bool,
) -> None:
    descriptor = tmp_path / "descriptor.xml"
    descriptor.write_text("<setup />", encoding="utf-8")
    observed_levels: list[int] = []
    if register_custom_level:
        monkeypatch.setattr(logging, "_nameToLevel", logging._nameToLevel.copy())
        monkeypatch.setattr(logging, "_levelToName", logging._levelToName.copy())
        logging.addLevelName(expected_level, "NOTICE")

    monkeypatch.setattr(runner, "bootstrap_process_title", lambda: None)
    monkeypatch.setattr(runner, "set_main_process_title", lambda _task_id, _descriptor: None)
    monkeypatch.setattr(runner, "setup_logger", lambda *, level, **_kwargs: observed_levels.append(level))
    monkeypatch.setattr(runner, "log_system_info", lambda: None)
    monkeypatch.setattr(runner, "log_memory_info", lambda _root: None)

    DataMimic(descriptor, args=args)

    assert observed_levels == [expected_level]


@pytest.mark.parametrize("log_level", [logging.NOTSET, 7], ids=["notset", "custom-integer"])
def test_runtime_passes_direct_integer_log_level_unchanged(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    log_level: int,
) -> None:
    descriptor = tmp_path / "descriptor.xml"
    descriptor.write_text("<setup />", encoding="utf-8")
    observed_levels: list[int] = []
    monkeypatch.setattr(runner, "bootstrap_process_title", lambda: None)
    monkeypatch.setattr(runner, "set_main_process_title", lambda _task_id, _descriptor: None)
    monkeypatch.setattr(runner, "setup_logger", lambda *, level, **_kwargs: observed_levels.append(level))
    monkeypatch.setattr(runner, "log_system_info", lambda: None)
    monkeypatch.setattr(runner, "log_memory_info", lambda _root: None)

    runner.create_run_session(RunRequest(descriptor_path=descriptor, log_level=log_level))

    assert observed_levels == [log_level]


def test_python_api_propagates_unexpected_log_level_conversion_error(monkeypatch) -> None:
    class BrokenNamespace(Namespace):
        @property
        def log_level(self) -> str:
            raise RuntimeError("broken log level")

    monkeypatch.setattr(runner, "bootstrap_process_title", lambda: None)
    monkeypatch.setattr(runner, "set_main_process_title", lambda _task_id, _descriptor: None)
    monkeypatch.setattr(runner, "setup_logger", lambda **_kwargs: None)
    monkeypatch.setattr(runner, "log_system_info", lambda: None)
    monkeypatch.setattr(runner, "log_memory_info", lambda _root: None)

    with pytest.raises(RuntimeError, match="broken log level"):
        DataMimic(Path("descriptor.xml"), args=BrokenNamespace())


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


@pytest.mark.parametrize(
    "property_values",
    [None, {}, {"tenant": "demo"}],
    ids=["none", "empty", "populated"],
)
def test_runtime_session_forwards_same_properties_to_parser_and_setup_task(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    property_values: dict[str, str] | None,
) -> None:
    descriptor = tmp_path / "descriptor.xml"
    descriptor.write_text("<setup />", encoding="utf-8")
    parsed_properties: list[dict[str, str] | None] = []
    setup_properties: list[dict[str, str] | None] = []
    original_parse = DescriptorParser.parse

    def parse_descriptor(
        path: Path,
        properties: dict[str, str] | None,
        environment: Literal["development", "production"],
        *,
        profile_loader: object,
    ) -> SetupStatement:
        parsed_properties.append(properties)
        return original_parse(path, properties, environment, profile_loader=profile_loader)

    class SetupTaskStub:
        def __init__(self, *, properties: dict[str, str] | None, **_kwargs: object) -> None:
            setup_properties.append(properties)

        def execute(self) -> None:
            pass

    monkeypatch.setattr(runner.DescriptorParser, "parse", parse_descriptor)
    monkeypatch.setattr(runner, "SetupTask", SetupTaskStub)
    session = runner.create_run_session(
        RunRequest(descriptor_path=descriptor, platform_props=property_values, test_mode=True)
    )

    session.execute()

    assert len(parsed_properties) == len(setup_properties) == 1
    assert parsed_properties[0] is property_values
    assert setup_properties[0] is property_values


def test_load_descriptor_properties_reads_found_file_and_defaults_when_missing(tmp_path: Path) -> None:
    descriptor = tmp_path / "model.xml"
    properties_file = tmp_path / "conf" / "environment.env.properties"
    properties_file.parent.mkdir()
    properties_file.write_text("# ignored\nuser = alice\nurl=https://example.test?a=b\n", encoding="utf-8")

    assert runtime_api.load_descriptor_properties(descriptor) == {
        "user": "alice",
        "url": "https://example.test?a=b",
    }
    assert runtime_api.load_descriptor_properties(tmp_path / "missing" / "model.xml") == {}


def test_load_descriptor_properties_preserves_parser_dictionary_identity(tmp_path: Path, monkeypatch) -> None:
    descriptor = tmp_path / "model.xml"
    properties: dict[str, str] = {"key": "value"}
    paths: list[Path] = []

    def parse(path: Path) -> dict[str, str]:
        paths.append(path)
        return properties

    monkeypatch.setattr(runtime_api, "parse_properties", parse)

    result = runtime_api.load_descriptor_properties(descriptor)

    assert type(result) is dict
    assert result is properties
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
    assert requests[0].platform_props == {"tenant": "demo"}
    assert type(requests[0].platform_props) is dict
    assert requests[0].platform_configs is not None
    assert requests[0].platform_configs.root == {"mode": "test"}
