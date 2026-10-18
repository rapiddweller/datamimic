"""Invalid descriptor input keeps portable error identity through runtime and CLI."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from datamimic_ce.engine.runtime.api import run
from datamimic_ce.engine.runtime.contracts import RunRequest
from datamimic_ce.errors import ParserValidationError, TaskConfigError
from datamimic_ce.interfaces.cli._app import app


@pytest.mark.parametrize(
    "body,element,attribute",
    [
        ('<iterate name="rows" count="1"/>', "iterate", "source"),
        (
            '<generate name="rows" count="1"><reference name="id" source="db" sourceType="customers"/></generate>',
            "reference",
            "sourceKey",
        ),
        (
            '<generate name="rows" count="1">'
            '<reference name="id" source="db" sourceType="customers" sourceKey="id">'
            '<field sourceKey="id" target="id"/>'
            "</reference>"
            "</generate>",
            "reference",
            "sourceKey",
        ),
        (
            '<generate name="rows" count="1">'
            '<reference name="id" source="db" sourceType="customers">'
            '<field sourceKey="id" target="id"/>'
            '<field sourceKey="id" target="other"/>'
            "</reference>"
            "</generate>",
            "field",
            "sourceKey",
        ),
        (
            '<generate name="rows" count="1">'
            '<reference name="id" source="db" sourceType="customers">'
            '<field sourceKey="id"/>'
            "</reference>"
            "</generate>",
            "field",
            None,
        ),
        (
            '<generate name="rows" start="2026-01-01T00:00:00+00:00" end="2026-01-01T03:00:00+00:00" interval="PT1H">'
            '<variable name="ts" entity="Person"/>'
            "</generate>",
            "variable",
            "name",
        ),
    ],
)
def test_parser_user_errors_have_portable_identity(
    tmp_path: Path, body: str, element: str, attribute: str | None
) -> None:
    path = tmp_path / "model.xml"
    path.write_text(f'<setup rngSeed="7">{body}</setup>')
    with pytest.raises(ParserValidationError) as caught:
        run(RunRequest(descriptor_path=path, test_mode=True))
    error = caught.value
    assert error.issue_code.value == "I605"
    assert error.location.element_tag == element
    assert error.location.attribute == attribute
    assert error.location.descriptor_path == "model.xml"
    assert str(tmp_path) not in str(error)
    if element == "field" and attribute is None:
        assert error.validation_errors[0]["loc"] == ("target",)
        assert error.__cause__ is not None


@pytest.mark.parametrize(
    "body,attribute,cause",
    [
        ('<execute type="python" script="1"/>', "script", None),
        ('<execute type="python">if :</execute>', None, SyntaxError),
    ],
)
def test_execute_user_errors_have_portable_identity(
    tmp_path: Path, body: str, attribute: str | None, cause: type[Exception] | None
) -> None:
    path = tmp_path / "model.xml"
    path.write_text(f'<setup rngSeed="7">{body}</setup>')
    with pytest.raises(TaskConfigError) as caught:
        run(RunRequest(descriptor_path=path, test_mode=True))
    error = caught.value
    assert error.issue_code.value == "I832"
    assert error.location.element_tag == "execute"
    assert error.location.attribute == attribute
    assert error.location.descriptor_path == "model.xml"
    assert str(tmp_path) not in str(error)
    if cause is not None:
        assert isinstance(error.__cause__, cause)


def test_cli_lint_keeps_the_source_attribute_repair_location(tmp_path: Path) -> None:
    path = tmp_path / "model.xml"
    path.write_text('<setup><iterate name="rows" count="1"/></setup>')
    result = CliRunner().invoke(app, ["authoring", "lint", str(path)])
    assert result.exit_code == 1
    diagnostic = json.loads(result.stdout)["diagnostics"][0]
    assert diagnostic["ce_error"] == {"error_code": "E011", "issue_code": "I605"}
    assert diagnostic["path"] == ["descriptor", "model.xml", "iterate", "attribute", "source"]


@pytest.mark.parametrize(
    "body,issue,attribute",
    [
        ('<execute type="sql" target="missing">SELECT 1</execute>', "I823", "target"),
        ('<execute type="bash">exit 3</execute>', "I894", None),
        ('<execute uri="missing.py"/>', "I824", "uri"),
    ],
)
def test_execute_target_and_resource_errors_are_catalogued(
    tmp_path: Path, body: str, issue: str, attribute: str | None
) -> None:
    path = tmp_path / "model.xml"
    path.write_text(f'<setup rngSeed="7">{body}</setup>')
    with pytest.raises(TaskConfigError) as caught:
        run(RunRequest(descriptor_path=path, test_mode=True))
    error = caught.value
    assert error.issue_code.value == issue
    assert error.location.element_tag == "execute"
    assert error.location.attribute == attribute
    assert str(tmp_path) not in str(error)
    if issue == "I823":
        assert isinstance(error.__cause__, KeyError)
    elif issue == "I824":
        assert isinstance(error.__cause__, FileNotFoundError)


def test_bash_warning_is_catalogued_once_per_process(tmp_path: Path, caplog, monkeypatch) -> None:
    import logging

    from datamimic_ce.errors import factory

    monkeypatch.setattr(factory, "_emitted_warnings", set())
    logger = logging.getLogger("DATAMIMIC")
    monkeypatch.setattr(logger, "propagate", False)
    logger.addHandler(caplog.handler)
    path = tmp_path / "model.xml"
    path.write_text(
        '<setup rngSeed="7"><execute type="bash">exit 0</execute><execute type="bash">exit 0</execute></setup>'
    )
    try:
        run(RunRequest(descriptor_path=path, test_mode=True))
    finally:
        logger.removeHandler(caplog.handler)
    assert sum("[W007]" in record.getMessage() for record in caplog.records) == 1
