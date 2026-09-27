from __future__ import annotations

from types import SimpleNamespace

import pytest

from datamimic_ce.engine.dsl.api import ExportOperation
from datamimic_ce.engine.io.exporters.core.exporter import Exporter
from datamimic_ce.engine.io.exporters.core.exporter_state_manager import ExporterStateManager
from datamimic_ce.engine.io.exporters.database.mongodb_exporter import MongoDBExporter
from datamimic_ce.engine.io.exporters.diagnostics.console_exporter import ConsoleExporter
from datamimic_ce.engine.io.exporters.diagnostics.test_result_exporter import TestResultExporter
from datamimic_ce.engine.io.exporters.exporter_util import ExporterUtil
from datamimic_ce.engine.io.exporters.formats.csv_exporter import CSVExporter
from datamimic_ce.engine.io.exporters.formats.json_exporter import JsonExporter
from datamimic_ce.engine.io.exporters.formats.txt_exporter import TXTExporter
from datamimic_ce.engine.io.exporters.formats.xml_exporter import XMLExporter
from datamimic_ce.engine.runtime.tasks.task_util import TaskUtil
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


def _root(stmt: SimpleNamespace, with_operation: list, without_operation: list) -> SimpleNamespace:
    return SimpleNamespace(
        task_exporters={
            stmt.full_name: {
                "page_count": 0,
                "with_operation": with_operation,
                "without_operation": without_operation,
            }
        }
    )


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

    TaskUtil.export_product_by_page(
        _root(stmt, [(mongo, ExportOperation.UPSERT)], [result]),
        stmt,
        {stmt.full_name: source_rows},
        ExporterStateManager(worker_id=1),
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

    TaskUtil.export_product_by_page(
        _root(stmt, [], [xml_exporter, json_exporter]),
        stmt,
        {stmt.full_name: source_rows},
        ExporterStateManager(worker_id=1),
    )

    assert received_xml[0][0] == ("products", source_rows)
    assert received_json[0][0] == ("products", [{"payload": "original"}])


def test_operation_errors_stay_direct_while_plain_export_errors_wrap_the_cause() -> None:
    stmt = _statement()
    source = {stmt.full_name: [{"id": 1}]}

    with pytest.raises(ValueError, match="Exporter does not support operation") as operation_error:
        TaskUtil.export_product_by_page(
            _root(stmt, [(Exporter(), ExportOperation.UPDATE)], []),
            stmt,
            source,
            ExporterStateManager(worker_id=1),
        )
    assert operation_error.value.__cause__ is None

    class BrokenConsoleExporter(ConsoleExporter):
        def consume(self, product: tuple) -> None:
            raise RuntimeError("plain export failed")

    with pytest.raises(ValueError, match="Error in exporter BrokenConsoleExporter: plain export failed") as plain_error:
        TaskUtil.export_product_by_page(
            _root(stmt, [], [BrokenConsoleExporter()]),
            stmt,
            source,
            ExporterStateManager(worker_id=1),
        )
    assert isinstance(plain_error.value.__cause__, RuntimeError)


def test_buffered_exporter_scalar_config_preserves_fallbacks_and_explicit_values(tmp_path) -> None:
    setup_context = MockSetupContext(task_id="dispatch", descriptor_dir=tmp_path)
    setup_context.default_separator = "|"
    setup_context.default_line_separator = "\n"
    setup_context.default_encoding = "utf-8"

    csv_default = ExporterUtil.get_exporter_by_name(setup_context, "CSV", _statement(), {})
    txt_default = ExporterUtil.get_exporter_by_name(setup_context, "TXT", _statement(), {})
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

    stmt = _statement(export_uri="published")
    csv_explicit = ExporterUtil.get_exporter_by_name(
        setup_context,
        "CSV",
        stmt,
        {"chunk_size": 7, "encoding": "latin-1", "delimiter": ";", "line_terminator": "\r\n"},
    )
    txt_explicit = ExporterUtil.get_exporter_by_name(
        setup_context,
        "TXT",
        stmt,
        {"chunk_size": 7, "encoding": "latin-1", "separator": ";", "line_terminator": "\r\n"},
    )
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
