from pathlib import Path

import pytest

from datamimic_ce.engine.runtime.api import create_run_session
from datamimic_ce.engine.runtime.contracts import RunRequest
from datamimic_ce.errors import ErrorCode, IncludeError, UserErrorBase


@pytest.mark.parametrize("dynamic", [False, True])
def test_setup_xml_include_executes_resolved_child(tmp_path: Path, dynamic: bool) -> None:
    (tmp_path / "child.xml").write_text(
        '<setup><generate name="child" count="2"><key name="value" constant="ok"/></generate></setup>',
        encoding="utf-8",
    )
    descriptor = tmp_path / "main.xml"
    uri = "{include_path}" if dynamic else "child.xml"
    descriptor.write_text(
        f'<setup rngSeed="1"><variable name="include_path" constant="child.xml"/><include uri="{uri}"/></setup>',
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

    with pytest.raises(FileNotFoundError, match=missing) as caught:
        create_run_session(RunRequest(descriptor_path=descriptor, test_mode=True)).execute()
    error = caught.value
    assert isinstance(error, IncludeError)
    assert isinstance(error, UserErrorBase)
    assert error.code is ErrorCode.INCLUDE_ERROR
    assert error.issue_code.value == "I201"
    assert error.location.element_tag == "include"
    assert error.location.attribute == "uri"
    assert error.location.descriptor_path == "main.xml"
    assert isinstance(error.__cause__, FileNotFoundError)
    assert str(tmp_path) not in str(error)


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


def test_nested_include_keeps_missing_inner_resource_identity(tmp_path: Path) -> None:
    (tmp_path / "child.xml").write_text('<setup><include uri="inner.properties"/></setup>', encoding="utf-8")
    descriptor = tmp_path / "main.xml"
    descriptor.write_text('<setup><include uri="child.xml"/></setup>', encoding="utf-8")

    with pytest.raises(FileNotFoundError, match="inner.properties") as caught:
        create_run_session(RunRequest(descriptor_path=descriptor, test_mode=True)).execute()
    assert isinstance(caught.value, IncludeError)
    assert caught.value.issue_code.value == "I201"
    assert "Include file 'child.xml' not found" not in str(caught.value)
    assert str(tmp_path) not in str(caught.value)


def test_included_execution_does_not_relabel_missing_runtime_resource(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "child.xml").write_text(
        '<setup><execute type="python">open("missing_runtime_resource.txt")</execute></setup>', encoding="utf-8"
    )
    descriptor = tmp_path / "main.xml"
    descriptor.write_text('<setup><include uri="child.xml"/></setup>', encoding="utf-8")

    with pytest.raises(FileNotFoundError, match="missing_runtime_resource.txt") as caught:
        create_run_session(RunRequest(descriptor_path=descriptor, test_mode=True)).execute()
    assert type(caught.value) is FileNotFoundError
    assert not isinstance(caught.value, IncludeError)
