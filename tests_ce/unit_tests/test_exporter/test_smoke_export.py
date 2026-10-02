import pytest

from datamimic_ce.engine.io.api import smoke_export
from datamimic_ce.engine.io.contracts import SmokeExportRequest
from datamimic_ce.engine.io.exporters import registry as exporter_registry


def test_smoke_export_writes_and_counts_buffered_rows(tmp_path) -> None:
    rows = [{"id": 1}]
    params = {"delimiter": ";"}
    request = SmokeExportRequest(
        descriptor_dir=tmp_path,
        task_id="smoke_test",
        basename="rows",
        full_name="rows",
        rows=rows,
        exporter_name="CSV",
        params=params,
        default_separator="|",
        default_line_separator="\n",
    )

    assert request.rows is rows
    assert request.params is params
    assert smoke_export(request) == 1


@pytest.mark.parametrize(
    ("exporter", "params", "default_separator", "default_line_separator", "expected"),
    [
        ("CSV", {}, ";", "\n", b"id;label\r\n1;x\r\n"),
        ("CSV", {"delimiter": ";"}, "||", "\n", b"id;label\r\n1;x\r\n"),
        ("TXT", {}, "|", "\r\n", b"rows: {'id': 1}\r\n"),
        ("TXT", {"line_terminator": ";"}, "|", "\r\n", b"rows: {'id': 1};"),
    ],
)
def test_smoke_export_uses_setup_defaults_and_target_precedence(
    tmp_path,
    exporter: str,
    params: dict[str, object],
    default_separator: str,
    default_line_separator: str,
    expected: bytes,
) -> None:
    request = SmokeExportRequest(
        descriptor_dir=tmp_path,
        task_id="smoke_test",
        basename="rows",
        full_name="rows",
        rows=[{"id": 1, "label": "x"}] if exporter == "CSV" else [{"id": 1}],
        exporter_name=exporter,
        params=params,
        default_separator=default_separator,
        default_line_separator=default_line_separator,
    )

    assert smoke_export(request) == 1
    artifacts = list(tmp_path.glob(f"temp_result_smoke_test_pid_1_exporter_{exporter.lower()}_product_rows/*"))
    assert len(artifacts) == 1
    assert artifacts[0].read_bytes() == expected


def test_smoke_export_preserves_nested_values_and_copies_only_exporter_options(
    tmp_path, monkeypatch
) -> None:
    opaque = object()
    nested = {"opaque": opaque}
    rows = [{"nested": nested}]
    params = {"chunk_size": 2, "custom": nested}
    observed = []

    class RecordingExporter:
        def __init__(self, config, exporter_params):
            observed.append(("init", config, exporter_params))

        def consume(self, product, full_name, state_manager):
            observed.append(("consume", product, full_name, state_manager.worker_id))

        def finalize_chunks(self, worker_id):
            observed.append(("finalize", worker_id))

        def count_buffered_rows(self, worker_id):
            observed.append(("count", worker_id))
            return 1

    monkeypatch.setitem(exporter_registry._BUFFERED_EXPORTERS, "JSON", RecordingExporter)
    request = SmokeExportRequest(
        descriptor_dir=tmp_path,
        task_id="smoke_test",
        basename="rows",
        full_name="parent|rows",
        rows=rows,
        exporter_name="JSON",
        params=params,
        default_separator="|",
        default_line_separator="\n",
    )

    assert smoke_export(request) == 1
    assert request.rows is rows
    assert request.params is params
    _, config, exporter_params = observed[0]
    assert exporter_params == params and exporter_params is not params
    assert exporter_params["custom"] is nested
    assert (
        config.product_name,
        config.chunk_size,
        config.encoding,
        config.export_uri,
        config.default_encoding,
        config.default_separator,
        config.default_line_separator,
        config.descriptor_dir,
        config.task_id,
        config.use_mp,
        config.track_serialized_rows,
    ) == ("rows", 2, None, None, "utf-8", "|", "\n", tmp_path, "smoke_test", False, True)
    assert observed[1][0] == "consume"
    assert observed[1][1][0] == "rows" and observed[1][1][1] is rows
    assert observed[1][2:] == ("parent|rows", 1)
    assert rows[0]["nested"]["opaque"] is opaque
    assert observed[2:] == [("finalize", 1), ("count", 1)]


@pytest.mark.parametrize(
    ("params", "message"),
    [
        ({"chunk_size": "2"}, "chunk_size target option must be an integer"),
        ({"encoding": 3}, "encoding target option must be a string"),
    ],
)
def test_smoke_export_rejects_invalid_native_options(tmp_path, params, message) -> None:
    request = SmokeExportRequest(
        descriptor_dir=tmp_path,
        task_id="smoke_test",
        basename="rows",
        full_name="rows",
        rows=[{"id": 1}],
        exporter_name="JSON",
        params=params,
        default_separator="|",
        default_line_separator="\n",
    )

    with pytest.raises(TypeError, match=message):
        smoke_export(request)


def test_smoke_export_unknown_exporter_keeps_registry_lookup_error(tmp_path) -> None:
    request = SmokeExportRequest(
        descriptor_dir=tmp_path,
        task_id="smoke_test",
        basename="rows",
        full_name="rows",
        rows=[{"id": 1}],
        exporter_name="NOPE",
        params={},
        default_separator="|",
        default_line_separator="\n",
    )

    with pytest.raises(KeyError, match="NOPE"):
        smoke_export(request)


@pytest.mark.parametrize("failure", ["consume", "finalize"])
def test_smoke_export_propagates_exporter_failures_in_order(tmp_path, monkeypatch, failure) -> None:
    observed = []

    class FailingExporter:
        def __init__(self, config, exporter_params):
            pass

        def consume(self, product, full_name, state_manager):
            observed.append("consume")
            if failure == "consume":
                raise RuntimeError("consume failed")

        def finalize_chunks(self, worker_id):
            observed.append("finalize")
            if failure == "finalize":
                raise RuntimeError("finalize failed")

        def count_buffered_rows(self, worker_id):
            observed.append("count")
            return 1

    monkeypatch.setitem(exporter_registry._BUFFERED_EXPORTERS, "JSON", FailingExporter)
    request = SmokeExportRequest(
        descriptor_dir=tmp_path,
        task_id="smoke_test",
        basename="rows",
        full_name="rows",
        rows=[{"id": 1}],
        exporter_name="JSON",
        params={},
        default_separator="|",
        default_line_separator="\n",
    )

    with pytest.raises(RuntimeError, match=f"{failure} failed"):
        smoke_export(request)
    assert observed == (["consume"] if failure == "consume" else ["consume", "finalize"])
