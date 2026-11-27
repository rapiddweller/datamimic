from pathlib import Path

import pytest

from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest


def _run(project_dir: Path, filename: str):
    DataMimicTest(test_dir=project_dir, filename=filename, capture_test_result=True).test_with_timer()


def test_exporturi_puts_the_file_under_that_prefix(project_dir):
    _run(project_dir, "csv_uri.xml")
    output = project_dir / "output"
    under_prefix = list((output / "reports" / "2026").glob("rows*.csv"))
    assert under_prefix, (
        f"no rows.csv under output/reports/2026 (tree: {[str(p.relative_to(project_dir)) for p in output.rglob('*.csv')]})"
    )


def test_without_exporturi_the_default_task_id_dir_is_unchanged(project_dir):
    _run(project_dir, "csv_default.xml")
    # not under a 'reports' prefix; still lands somewhere under output/
    assert list((project_dir / "output").rglob("rows*.csv"))
    assert not (project_dir / "output" / "reports").exists()


@pytest.mark.parametrize(
    "f,msg",
    [
        ("uri_traversal.xml", r"path|traversal|\.\."),
        ("uri_scheme.xml", r"scheme|://"),
    ],
)
def test_invalid_exporturi_is_rejected(project_dir, f, msg):
    with pytest.raises(Exception, match=msg):
        _run(project_dir, f)


def test_exporturi_works_for_json_too(project_dir):
    _run(project_dir, "json_uri.xml")
    assert list((project_dir / "output" / "out" / "json").glob("rows*.json"))
