from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

import pytest

from datamimic_ce.engine.dsl.api import (
    EXPORTER_CSV,
    EXPORTER_DBUNIT,
    EXPORTER_FIXED_WIDTH,
    EXPORTER_JSON,
    EXPORTER_TXT,
    EXPORTER_XLSX,
    EXPORTER_XML,
    ExportOperation,
    GenerateStatement,
)
from datamimic_ce.engine.dsl.model.generation.generate_model import GenerateModel
from datamimic_ce.engine.io.api import Exporter, ExportSession, buffered_exporter_names
from datamimic_ce.engine.io.contracts import ExportMetadata
from datamimic_ce.engine.io.exporters import registry as exporter_registry
from datamimic_ce.engine.io.exporters import session as export_session_module
from datamimic_ce.engine.io.exporters.core.exporter_config import ExporterConfig
from datamimic_ce.engine.io.exporters.database.mongodb_exporter import MongoDBExporter
from datamimic_ce.engine.io.exporters.diagnostics.console_exporter import ConsoleExporter
from datamimic_ce.engine.io.exporters.diagnostics.test_result_exporter import TestResultExporter
from datamimic_ce.engine.io.exporters.formats.csv_exporter import CSVExporter
from datamimic_ce.engine.io.exporters.formats.json_exporter import JsonExporter
from datamimic_ce.engine.io.exporters.formats.txt_exporter import TXTExporter
from datamimic_ce.engine.io.exporters.formats.xml_exporter import XMLExporter
from datamimic_ce.engine.io.exporters.registry import create_exporter_list
from datamimic_ce.engine.runtime.tasks.generate import export_order
from tests_ce.unit_tests.test_exporter.exporter_test_util import MockSetupContext


def _statement(*, export_uri: str | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        full_name="products",
        name="products",
        target_entity=None,
        selector=None,
        type=None,
        export_uri=export_uri,
        sub_statements=[],
    )


def _session(stmt: SimpleNamespace, with_operation: list, without_operation: list) -> ExportSession:
    session = ExportSession(worker_id=1)
    session._register_exporters(stmt.full_name, with_operation, without_operation)
    return session


def test_lazy_capture_rejects_wrong_exporter_type() -> None:
    context = SimpleNamespace(test_result_exporter=Exporter())

    with pytest.raises(TypeError, match="Test capture requires TestResultExporter"):
        exporter_registry.capture_test_results(context, {"rows": []})


def test_memstore_write_rejects_wrong_exporter_type() -> None:
    manager = SimpleNamespace(contain=lambda _target: True, get_memstore=lambda _target: Exporter())
    context = SimpleNamespace(memstore_manager=manager)

    with pytest.raises(TypeError, match="Memstore target requires Memstore exporter"):
        exporter_registry.consume_memstore_target(context, ["mem"], None, None, "rows", "rows", {"rows": []})


def test_mongodb_upsert_replaces_rows_for_subsequent_plain_exporter(monkeypatch: pytest.MonkeyPatch) -> None:
    stmt = _statement()
    mongo = object.__new__(MongoDBExporter)
    captured_upsert: list[tuple] = []

    def upsert(_self: MongoDBExporter, product: tuple) -> tuple:
        captured_upsert.append(product)
        return "products", [{"id": 1, "state": "modified"}]

    monkeypatch.setattr(MongoDBExporter, "upsert", upsert)
    result = TestResultExporter()
    source_rows = [{"id": 1, "state": "original"}]

    export_order.export_product_by_page(
        stmt,
        {stmt.full_name: source_rows},
        _session(stmt, [(mongo, ExportOperation.UPSERT)], [result]),
    )

    assert captured_upsert == [("products", source_rows)]
    assert result.get_result() == {"products": [{"id": 1, "state": "modified"}]}


def test_xml_receives_original_rows_while_other_buffered_exporters_receive_converted_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stmt = _statement()
    xml_exporter = object.__new__(XMLExporter)
    json_exporter = object.__new__(JsonExporter)
    received_xml: list[tuple] = []
    received_json: list[tuple] = []
    monkeypatch.setattr(XMLExporter, "consume", lambda self, *args: received_xml.append(args))
    monkeypatch.setattr(JsonExporter, "consume", lambda self, *args: received_json.append(args))
    source_rows = [{"payload": {"#text": "original"}}]

    export_order.export_product_by_page(
        stmt,
        {stmt.full_name: source_rows},
        _session(stmt, [], [xml_exporter, json_exporter]),
    )

    assert received_xml[0][0] == ("products", source_rows)
    assert received_xml[0][0][1] is source_rows
    assert received_xml[0][0][1][0] is source_rows[0]
    assert received_json[0][0] == ("products", [{"payload": "original"}])


def test_statement_metadata_reaches_json_but_not_xml_exporters(monkeypatch: pytest.MonkeyPatch) -> None:
    stmt = _statement()
    stmt.target_entity = "target"
    stmt.selector = "id=1"
    stmt.type = "kind"
    xml_exporter = object.__new__(XMLExporter)
    json_exporter = object.__new__(JsonExporter)
    received_xml: list[tuple] = []
    received_json: list[tuple] = []
    monkeypatch.setattr(XMLExporter, "consume", lambda self, *args: received_xml.append(args))
    monkeypatch.setattr(JsonExporter, "consume", lambda self, *args: received_json.append(args))

    export_order.export_product_by_page(
        stmt,
        {stmt.full_name: [{"id": 1}]},
        _session(stmt, [], [xml_exporter, json_exporter]),
    )

    expected_metadata = {"target_entity": "target", "selector": "id=1", "type": "kind"}
    assert received_xml[0][0] == ("products", [{"id": 1}])
    assert received_json[0][0] == ("products", [{"id": 1}], expected_metadata)


def test_operation_errors_stay_direct_while_plain_export_errors_wrap_the_cause() -> None:
    stmt = _statement()
    source = {stmt.full_name: [{"id": 1}]}

    with pytest.raises(ValueError, match="Exporter does not support operation") as operation_error:
        export_order.export_product_by_page(
            stmt,
            source,
            _session(stmt, [(Exporter(), ExportOperation.UPDATE)], []),
        )
    assert operation_error.value.__cause__ is None

    class BrokenConsoleExporter(ConsoleExporter):
        def consume(self, product: tuple) -> None:
            raise RuntimeError("plain export failed")

    with pytest.raises(ValueError, match="Error in exporter BrokenConsoleExporter: plain export failed") as plain_error:
        export_order.export_product_by_page(
            stmt,
            source,
            _session(stmt, [], [BrokenConsoleExporter()]),
        )
    assert isinstance(plain_error.value.__cause__, RuntimeError)


def test_buffered_exporter_scalar_config_preserves_fallbacks_and_explicit_values(tmp_path) -> None:
    setup_context = MockSetupContext(task_id="dispatch", descriptor_dir=tmp_path)
    setup_context.default_separator = "|"
    setup_context.default_line_separator = "\n"
    setup_context.default_encoding = "utf-8"

    _, defaults = create_exporter_list(setup_context, "products", None, ["CSV", "TXT"])
    csv_default, txt_default = defaults
    assert isinstance(csv_default, CSVExporter)
    assert isinstance(txt_default, TXTExporter)
    assert (csv_default.chunk_size, csv_default.encoding, csv_default._export_uri, csv_default.delimiter) == (
        None,
        "utf-8",
        None,
        "|",
    )
    assert (txt_default.chunk_size, txt_default.encoding, txt_default._export_uri, txt_default.separator) == (
        None,
        "utf-8",
        None,
        "|",
    )

    _, explicit = create_exporter_list(
        setup_context,
        "products",
        "published",
        [
            "CSV(chunk_size=7, encoding='latin-1', delimiter=';', line_terminator='\\r\\n')",
            "TXT(chunk_size=7, encoding='latin-1', separator=';', line_terminator='\\r\\n')",
        ],
    )
    csv_explicit, txt_explicit = explicit
    assert isinstance(csv_explicit, CSVExporter)
    assert isinstance(txt_explicit, TXTExporter)
    assert (csv_explicit.chunk_size, csv_explicit.encoding, csv_explicit._export_uri, csv_explicit.delimiter) == (
        7,
        "latin-1",
        "published",
        ";",
    )
    assert (txt_explicit.chunk_size, txt_explicit.encoding, txt_explicit._export_uri, txt_explicit.separator) == (
        7,
        "latin-1",
        "published",
        ";",
    )


def test_buffered_exporter_public_names_and_config_scalars(tmp_path) -> None:
    assert buffered_exporter_names() == frozenset(
        {
            EXPORTER_CSV,
            EXPORTER_DBUNIT,
            EXPORTER_FIXED_WIDTH,
            EXPORTER_JSON,
            EXPORTER_TXT,
            EXPORTER_XLSX,
            EXPORTER_XML,
        }
    )

    default = ExporterConfig(
        product_name="products",
        chunk_size=None,
        encoding=None,
        export_uri=None,
        default_encoding="utf-8",
        default_separator="|",
        default_line_separator="\n",
        descriptor_dir=tmp_path,
        task_id="dispatch",
        use_mp=False,
    )
    explicit = ExporterConfig(
        product_name="products",
        chunk_size=7,
        encoding="latin-1",
        export_uri="published",
        default_encoding="utf-8",
        default_separator="|",
        default_line_separator="\n",
        descriptor_dir=tmp_path,
        task_id="dispatch",
        use_mp=False,
        track_serialized_rows=True,
    )
    assert (
        default.product_name,
        default.chunk_size,
        default.encoding,
        default.export_uri,
        default.track_serialized_rows,
    ) == (
        "products",
        None,
        None,
        None,
        False,
    )
    assert (
        explicit.product_name,
        explicit.chunk_size,
        explicit.encoding,
        explicit.export_uri,
        explicit.track_serialized_rows,
    ) == (
        "products",
        7,
        "latin-1",
        "published",
        True,
    )


def test_exporter_factory_preserves_target_parse_and_unknown_operation_errors(tmp_path) -> None:
    setup_context = MockSetupContext(task_id="dispatch", descriptor_dir=tmp_path)
    statement = _statement()
    with pytest.raises(ValueError, match="Error parsing target string: Non-literal parameter found") as malformed:
        create_exporter_list(setup_context, statement.name, statement.export_uri, ["CSV(chunk_size=runtime_value)"])
    assert isinstance(malformed.value.__cause__, ValueError)

    with pytest.raises(
        ValueError,
        match=r"Unknown client operation 'patch' in target 'db.patch'.*plain client id inserts.",
    ) as unknown_operation:
        create_exporter_list(setup_context, statement.name, statement.export_uri, ["db.patch"])
    assert unknown_operation.value.__cause__ is None


def test_conversion_failure_precedes_registration_lookup_and_nested_writes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parent = GenerateStatement(GenerateModel(name="parents", count="1"), None)
    child = GenerateStatement(GenerateModel(name="children", count="1"), parent)
    parent.sub_statements = [child]
    child_result = TestResultExporter()
    session = ExportSession(worker_id=1)
    session._register_exporters(child.full_name, [], [child_result])

    def fail_conversion(_row: dict[str, object]) -> object:
        raise ValueError("unserializable XML row")

    monkeypatch.setattr(export_session_module, "convert_xml_dict_to_json_dict", fail_conversion)

    with pytest.raises(ValueError, match="unserializable XML row"):
        export_order.export_product_by_page(
            parent,
            {parent.full_name: [{"payload": {"#text": "parent"}}], child.full_name: [{"id": 1}]},
            session,
        )

    assert child_result.get_result() == {}


def test_export_session_registers_targets_through_registry_factory() -> None:
    result = TestResultExporter()
    setup_context = SimpleNamespace(test_result_exporter=result)
    session = ExportSession(worker_id=1)

    session.register(setup_context, "products", "products", None, ["TestResultExporter"])
    page = session.prepare_page("products", "products", [{"id": 1}], {})
    session.dispatch_page("products", page)

    assert result.get_result() == {"products": [{"id": 1}]}


def test_test_result_exporter_accepts_variadic_tuple_tail_and_keeps_rows() -> None:
    result = TestResultExporter()
    rows = [{"id": 1}]

    result.consume(("products", rows, {"target_entity": "orders"}, "extra metadata"))

    captured = result.get_result()
    assert captured == {"products": rows}
    assert captured["products"][0] is rows[0]


def test_prepare_page_preserves_metadata_tuple_shape_and_original_rows() -> None:
    session = ExportSession(worker_id=1)
    native = object()
    nested = object()
    price = Decimal("1.20")
    rows: list[dict[str, object]] = [
        {"#text": native},
        {"price": price, "child": {"#text": nested}, "items": [{"#text": nested}], "@flag": "x"},
    ]
    metadata: ExportMetadata = {"target_entity": "orders"}
    result = TestResultExporter()
    session._register_exporters("products", [], [result])

    without_metadata, original_rows = session.prepare_page("products", "products", rows, {})
    page = session.prepare_page("products", "products", rows, metadata)
    with_metadata, metadata_rows = page

    converted = [native, {"price": price, "child": nested, "items": [nested]}]
    assert without_metadata == ("products", converted)
    assert with_metadata == ("products", converted, metadata)
    assert with_metadata[2] is metadata
    assert with_metadata[1][0] is native
    assert with_metadata[1][1]["price"] is price
    assert with_metadata[1][1]["child"] is nested
    assert with_metadata[1][1]["items"][0] is nested
    assert original_rows is rows
    assert metadata_rows is rows
    assert metadata_rows[0]["#text"] is native
    assert metadata_rows[1]["child"]["#text"] is nested

    session.dispatch_page("products", page)
    captured = result.get_result()["products"]
    assert captured == converted
    assert captured[0] is native
    assert captured[1] is with_metadata[1][1]
    assert session.prepare_page("products", "products", [], {})[0] == ("products", [])


@pytest.mark.parametrize("rows, error", [([{1: "bad"}], AttributeError), ([object()], TypeError)])
def test_prepare_page_preserves_invalid_raw_row_errors(rows, error) -> None:
    session = ExportSession(worker_id=1)
    session._register_exporters("products", [], [])

    with pytest.raises(error) as raised:
        session.prepare_page("products", "products", rows, {})

    assert raised.value.__cause__ is None


def test_prepare_page_preserves_dictionary_subclass_errors() -> None:
    failure = RuntimeError("native items failure")

    class BrokenDict(dict):
        def items(self):
            raise failure

    session = ExportSession(worker_id=1)
    session._register_exporters("products", [], [])

    with pytest.raises(RuntimeError) as raised:
        session.prepare_page("products", "products", [BrokenDict()], {})

    assert raised.value is failure


def test_missing_registration_fails_before_nested_writes() -> None:
    parent = GenerateStatement(GenerateModel(name="parents", count="1"), None)
    child = GenerateStatement(GenerateModel(name="children", count="1"), parent)
    parent.sub_statements = [child]
    child_result = TestResultExporter()
    session = ExportSession(worker_id=1)
    session._register_exporters(child.full_name, [], [child_result])

    with pytest.raises(KeyError, match=parent.full_name):
        export_order.export_product_by_page(
            parent,
            {parent.full_name: [{"id": 1}], child.full_name: [{"id": 2}]},
            session,
        )

    assert child_result.get_result() == {}
