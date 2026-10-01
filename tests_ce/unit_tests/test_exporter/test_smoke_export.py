import pytest

from datamimic_ce.engine.io.api import smoke_export
from datamimic_ce.engine.io.contracts import (
    SmokeExportParameters,
    SmokeExportRequest,
    SmokeExportRows,
)


def test_smoke_export_writes_and_counts_buffered_rows(tmp_path) -> None:
    rows = [{"id": 1}]
    params = {"delimiter": ";"}
    request = SmokeExportRequest(
        descriptor_dir=tmp_path,
        task_id="smoke_test",
        basename="rows",
        full_name="rows",
        rows=SmokeExportRows.model_construct(root=rows),
        exporter_name="CSV",
        params=SmokeExportParameters.model_construct(root=params),
        default_separator="|",
        default_line_separator="\n",
    )

    assert request.rows.root is rows
    assert request.params.root is params
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
        rows=SmokeExportRows.model_construct(
            root=[{"id": 1, "label": "x"}] if exporter == "CSV" else [{"id": 1}]
        ),
        exporter_name=exporter,
        params=SmokeExportParameters.model_construct(root=params),
        default_separator=default_separator,
        default_line_separator=default_line_separator,
    )

    assert smoke_export(request) == 1
    artifacts = list(tmp_path.glob(f"temp_result_smoke_test_pid_1_exporter_{exporter.lower()}_product_rows/*"))
    assert len(artifacts) == 1
    assert artifacts[0].read_bytes() == expected
