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
    )

    assert request.rows.root is rows
    assert request.params.root is params
    assert smoke_export(request) == 1
