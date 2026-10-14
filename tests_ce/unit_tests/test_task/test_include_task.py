from pathlib import Path

import pytest

from datamimic_ce.engine.runtime.api import create_run_session
from datamimic_ce.engine.runtime.contracts import RunRequest


@pytest.mark.parametrize("dynamic", [False, True])
def test_setup_xml_include_executes_resolved_child(tmp_path: Path, dynamic: bool) -> None:
    (tmp_path / "child.xml").write_text(
        '<setup><generate name="child" count="2"><key name="value" constant="ok"/></generate></setup>',
        encoding="utf-8",
    )
    descriptor = tmp_path / "main.xml"
    uri = "{include_path}" if dynamic else "child.xml"
    descriptor.write_text(
        '<setup rngSeed="1"><variable name="include_path" constant="child.xml"/>'
        f'<include uri="{uri}"/></setup>',
        encoding="utf-8",
    )

    result = create_run_session(RunRequest(descriptor_path=descriptor, test_mode=True)).execute()

    assert result.captured == {"child": [{"value": "ok"}, {"value": "ok"}]}


@pytest.mark.parametrize("dynamic", [False, True])
def test_setup_properties_include_supplies_row_count(tmp_path: Path, dynamic: bool) -> None:
    (tmp_path / "rows.properties").write_text("row_count=2\n", encoding="utf-8")
    descriptor = tmp_path / "main.xml"
    uri = "{include_path}" if dynamic else "rows.properties"
    descriptor.write_text(
        '<setup rngSeed="1"><variable name="include_path" constant="rows.properties"/>'
        f'<include uri="{uri}"/>'
        '<generate name="rows" count="{row_count}"><key name="value" constant="ok"/></generate></setup>',
        encoding="utf-8",
    )

    result = create_run_session(RunRequest(descriptor_path=descriptor, test_mode=True)).execute()

    assert result.captured == {"rows": [{"value": "ok"}, {"value": "ok"}]}


@pytest.mark.parametrize("dynamic", [False, True])
@pytest.mark.parametrize("extension", ["xml", "properties"])
def test_setup_include_preserves_missing_file_error(tmp_path: Path, dynamic: bool, extension: str) -> None:
    missing = f"missing.{extension}"
    uri = "{include_path}" if dynamic else missing
    descriptor = tmp_path / "main.xml"
    descriptor.write_text(
        f'<setup><variable name="include_path" constant="{missing}"/><include uri="{uri}"/></setup>',
        encoding="utf-8",
    )

    expected_path = "main.xml" if extension == "properties" and not dynamic else missing
    with pytest.raises(FileNotFoundError, match=expected_path):
        create_run_session(RunRequest(descriptor_path=descriptor, test_mode=True)).execute()


@pytest.mark.parametrize("dynamic", [False, True])
def test_generate_xml_include_executes_resolved_child(tmp_path: Path, dynamic: bool) -> None:
    (tmp_path / "child.xml").write_text(
        '<setup><generate name="child" count="2"><key name="value" constant="ok"/></generate></setup>',
        encoding="utf-8",
    )
    descriptor = tmp_path / "main.xml"
    uri = "{include_path}" if dynamic else "child.xml"
    descriptor.write_text(
        '<setup rngSeed="1"><variable name="include_path" constant="child.xml"/>'
        f'<generate name="outer" count="1"><include uri="{uri}"/></generate></setup>',
        encoding="utf-8",
    )

    result = create_run_session(RunRequest(descriptor_path=descriptor, test_mode=True)).execute()

    assert result.captured == {"outer": [{}], "child": [{"value": "ok"}, {"value": "ok"}]}
