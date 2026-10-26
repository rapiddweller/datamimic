"""Public failures disclose safe facts and stay inside their declared contracts."""

import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from xml.sax.saxutils import quoteattr

import pytest
import sqlalchemy
from typer.testing import CliRunner

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.domain.requests import PROJECT_ENTRY_PATH, RejectedBuild
from datamimic_ce.engine.runtime.api import run
from datamimic_ce.engine.runtime.contracts import RunRequest
from datamimic_ce.errors import IssueCode, OperationError, UserErrorBase
from datamimic_ce.interfaces.cli import app
from tests_ce.authoring_project import write_project

SENTINEL = "AUDIT_SYNTHETIC_PRIVATE_VALUE_583c"
EXPRESSIONS = (
    ("int(os.environ['AUDIT_ERROR_TOKEN'])", ValueError),
    ("{}[os.environ['AUDIT_ERROR_TOKEN']]", KeyError),
    ("os.__getattribute__(os.environ['AUDIT_ERROR_TOKEN'])", AttributeError),
)


def _run(tmp_path, body):
    path = tmp_path / "model.xml"
    path.write_text(f'<setup rngSeed="7">{body}</setup>', encoding="utf-8")
    return run(RunRequest(descriptor_path=path, test_mode=True, log_level=logging.CRITICAL))


@pytest.mark.parametrize("expression,cause_type", EXPRESSIONS)
def test_runtime_expression_errors_keep_native_cause_without_native_values(
    tmp_path, monkeypatch, expression, cause_type
):
    monkeypatch.setenv("AUDIT_ERROR_TOKEN", SENTINEL)
    with pytest.raises(UserErrorBase) as caught:
        _run(tmp_path, f'<generate name="rows" count="1"><key name="v" script={quoteattr(expression)}/></generate>')
    error = caught.value
    assert error.issue_code is IssueCode.TASK_EXPRESSION_EVAL_FAILED
    assert isinstance(error.__cause__, cause_type)
    assert SENTINEL in str(error.__cause__)
    assert SENTINEL not in str(error)
    assert error.location.element_tag == "key"
    assert error.location.attribute == "script"
    assert error.location.descriptor_path == "model.xml"


@pytest.mark.parametrize("expression,cause_type", EXPRESSIONS)
def test_cli_expression_errors_do_not_publish_native_values(tmp_path, expression, cause_type):
    path = tmp_path / "model.xml"
    path.write_text(
        '<setup rngSeed="7"><generate name="rows" count="1">'
        f'<key name="v" script={quoteattr(expression)}/></generate></setup>',
        encoding="utf-8",
    )
    response = subprocess.run(
        [sys.executable, "-m", "datamimic_ce.interfaces.cli", "run", str(path), "--test-mode"],
        cwd=tmp_path,
        env={
            **os.environ,
            "PYTHONPATH": str(Path(__file__).parents[2]),
            "AUDIT_ERROR_TOKEN": SENTINEL,
            "NO_COLOR": "1",
        },
        capture_output=True,
        text=True,
        timeout=30,
    )
    output = response.stdout + response.stderr
    assert response.returncode == 1
    assert "E013/I832" in output
    assert SENTINEL not in output
    assert "Traceback" not in output


def test_key_fallback_error_keeps_native_cause_without_native_text(tmp_path, monkeypatch):
    from datamimic_ce.engine.runtime.scripting import evaluation

    failure = ValueError(SENTINEL)

    def fail(*args, diagnostic_expression=None):
        raise failure

    monkeypatch.setattr(evaluation, "evaluate_python", fail)
    with pytest.raises(UserErrorBase) as caught:
        _run(tmp_path, '<generate name="rows" count="1"><key name="v" script="1"/></generate>')
    error = caught.value
    assert error.issue_code is IssueCode.TASK_SCRIPT_ERROR
    assert error.__cause__ is failure
    assert SENTINEL not in str(error)
    assert error.location.element_tag == "key"
    assert error.location.attribute == "script"


def test_key_invalid_result_reports_type_without_generated_values(tmp_path, monkeypatch):
    monkeypatch.setenv("AUDIT_ERROR_TOKEN", SENTINEL)
    with pytest.raises(UserErrorBase) as caught:
        _run(
            tmp_path,
            '<generate name="rows" count="1">'
            '<key name="v" script="[os.environ[&apos;AUDIT_ERROR_TOKEN&apos;]]"/></generate>',
        )
    error = caught.value
    assert error.issue_code is IssueCode.TASK_KEY_SCRIPT_INVALID_TYPE
    assert "list" in str(error)
    assert SENTINEL not in str(error)
    assert error.location.attribute == "script"


def _build(project):
    return create_authoring_application(project, descriptor_path=PROJECT_ENTRY_PATH).build()


@pytest.mark.parametrize("interval", ["P999999999999999999999D", "PT999999999999999999999S"])
@pytest.mark.parametrize("transport", ["python", "cli"])
def test_extreme_duration_is_a_typed_build_rejection(tmp_path, interval, transport):
    write_project(
        tmp_path,
        '<setup rngSeed="7"><generate name="rows" start="2026-01-01" end="2026-01-02" '
        f'interval="{interval}"><key name="v" constant="ok"/></generate></setup>',
    )
    if transport == "python":
        result = _build(tmp_path)
        assert isinstance(result, RejectedBuild)
        diagnostic = result.diagnostics[0].model_dump(mode="json")
    else:
        response = CliRunner().invoke(app, ["authoring", "build", str(tmp_path)])
        assert response.exit_code == 1
        result = json.loads(response.stdout)
        assert result["outcome"] == "rejected"
        diagnostic = result["diagnostics"][0]
    assert diagnostic["path"][-2:] == ["properties", "interval"]
    assert diagnostic["remediation"]


@pytest.mark.parametrize("transport", ["python", "cli"])
def test_extreme_decimal_quantum_is_a_typed_build_rejection(tmp_path, transport):
    write_project(
        tmp_path,
        '<setup rngSeed="7"><generate name="rows" count="1"><key name="v" type="decimal" '
        'min="1" max="2" granularity="1e999999999"/></generate></setup>',
    )
    if transport == "python":
        result = _build(tmp_path)
        assert isinstance(result, RejectedBuild)
        diagnostic = result.diagnostics[0].model_dump(mode="json")
    else:
        response = CliRunner().invoke(app, ["authoring", "build", str(tmp_path)])
        assert response.exit_code == 1
        result = json.loads(response.stdout)
        assert result["outcome"] == "rejected"
        diagnostic = result["diagnostics"][0]
    assert diagnostic["path"][-2:] == ["properties", "granularity"]
    assert diagnostic["remediation"]


def test_routed_database_count_acquisition_is_portable(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "db" / "audit.sqlite").mkdir(parents=True)
    with pytest.raises(OperationError) as caught:
        _run(
            tmp_path,
            '<database id="db" dbms="sqlite" database="audit"/>'
            '<generate name="rows" count="1" source="db" sourceEntity="missing"/>',
        )
    error = caught.value
    assert error.issue_code is IssueCode.OPERATION_EXECUTION_FAILED
    assert isinstance(error.__cause__, sqlalchemy.exc.OperationalError)
    assert "connection_failed" in str(error)
    assert error.location.element_tag == "generate"
    assert error.location.attribute == "sourceEntity"
    assert str(tmp_path) not in str(error)


def test_routed_headerless_weighted_source_is_portable(tmp_path):
    (tmp_path / "values.wgt.csv").write_text("a|1\nb|2\n")
    with pytest.raises(UserErrorBase) as caught:
        _run(tmp_path, '<generate name="rows" count="1" source="values.wgt.csv"/>')
    error = caught.value
    assert error.issue_code is IssueCode.SOURCE_INVALID_CSV
    assert error.location.element_tag == "generate"
    assert error.location.attribute == "source"
    assert "header" in str(error).lower()
    assert str(tmp_path) not in str(error)


@pytest.mark.parametrize("operation", ["reflection", "execution"])
def test_routed_database_count_native_failures_are_portable(tmp_path, monkeypatch, operation):
    from datamimic_ce.engine.io.clients.rdbms_client import RdbmsClient

    failure = sqlalchemy.exc.NoSuchTableError(SENTINEL)

    def fail(*args, **kwargs):
        raise failure

    if operation == "reflection":
        monkeypatch.setattr(RdbmsClient, "_get_metadata", fail)
    else:
        (tmp_path / "db").mkdir()
        import sqlite3

        with sqlite3.connect(tmp_path / "db/audit.sqlite") as connection:
            connection.execute("CREATE TABLE entries (id INTEGER)")
        monkeypatch.setattr(sqlalchemy.engine.Connection, "execute", fail)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(OperationError) as caught:
        _run(
            tmp_path,
            '<database id="db" dbms="sqlite" database="audit"/>'
            '<generate name="rows" count="1" source="db" sourceEntity="entries"/>',
        )
    error = caught.value
    assert error.__cause__ is failure
    assert error.issue_code is IssueCode.OPERATION_EXECUTION_FAILED
    assert "table_not_found" in str(error)
    assert SENTINEL not in str(error)
    assert error.location.element_tag == "generate"
    assert error.location.attribute == "sourceEntity"


@pytest.mark.parametrize(
    "attributes,attribute,error_code",
    [
        ('type="int"', "type", "E013"),
        ('type="float"', "type", "E013"),
        ('type="decimal"', "type", "E013"),
        ('inDateFormat="%Y"', "inDateFormat", "E003"),
        ('converter="Timestamp2Date"', "converter", "E013"),
    ],
)
def test_key_conversion_failures_keep_safe_facts_and_location(tmp_path, monkeypatch, attributes, attribute, error_code):
    monkeypatch.setenv("AUDIT_ERROR_TOKEN", SENTINEL)
    with pytest.raises(UserErrorBase) as caught:
        _run(
            tmp_path,
            '<generate name="rows" count="1">'
            f'<key name="v" script="os.environ[&apos;AUDIT_ERROR_TOKEN&apos;]" {attributes}/></generate>',
        )
    error = caught.value
    assert error.code.value == error_code
    assert error.__cause__ is not None
    assert SENTINEL not in str(error)
    assert error.location.element_tag == "key"
    assert error.location.attribute == attribute
    assert error.location.descriptor_path == "model.xml"


def test_routed_database_count_missing_table_is_portable(tmp_path, monkeypatch):
    import sqlite3

    monkeypatch.chdir(tmp_path)
    (tmp_path / "db").mkdir()
    with sqlite3.connect(tmp_path / "db/audit.sqlite"):
        pass
    with pytest.raises(OperationError) as caught:
        _run(
            tmp_path,
            '<database id="db" dbms="sqlite" database="audit"/>'
            '<generate name="rows" count="1" source="db" sourceEntity="missing"/>',
        )
    assert caught.value.issue_code is IssueCode.OPERATION_EXECUTION_FAILED
    assert caught.value.__cause__ is not None
    assert "table_not_found" in str(caught.value)
    assert caught.value.location.attribute == "sourceEntity"


@pytest.mark.parametrize("error_type", [NameError, AttributeError, KeyError])
def test_native_lookup_errors_without_metadata_keep_only_safe_failure_facts(error_type):
    from datamimic_ce.engine.runtime.scripting.evaluation import evaluate_python

    native = error_type(SENTINEL)

    def fail():
        raise native

    with pytest.raises(UserErrorBase) as caught:
        evaluate_python("fail()", {"fail": fail}, {})
    assert caught.value.__cause__ is native
    assert error_type.__name__ in str(caught.value)
    assert SENTINEL not in str(caught.value)


@pytest.mark.parametrize("error_type", [NameError, AttributeError])
def test_a_missing_name_is_shown_only_when_the_expression_text_holds_it(error_type):
    """Python-only: a called function that raises a name built from data cannot be written as a descriptor
    without a library that raises it on purpose, and this module owns the redaction boundary."""
    from datamimic_ce.engine.runtime.scripting.evaluation import evaluate_python

    def fail():
        raise error_type("lookup failed", name=SENTINEL)

    with pytest.raises(UserErrorBase) as caught:
        evaluate_python("fail()", {"fail": fail}, {})
    assert SENTINEL not in str(caught.value)


@pytest.mark.parametrize(
    "body,issue",
    [
        (
            '<generate name="rows" count="1">'
            '<key name="v" script="int(os.environ[&apos;AUDIT_ERROR_TOKEN&apos;])"/></generate>',
            IssueCode.TASK_EXPRESSION_EVAL_FAILED,
        ),
        (
            '<generate name="rows" count="1">'
            '<key name="v" type="int" script="os.environ[&apos;AUDIT_ERROR_TOKEN&apos;]"/></generate>',
            IssueCode.TASK_DATATYPE_INVALID,
        ),
        ('<generate name="rows" count="1" source="values.wgt.csv"/>', IssueCode.SOURCE_INVALID_CSV),
        (
            '<database id="db" dbms="sqlite" database="audit"/>'
            '<generate name="rows" count="1" source="db" sourceEntity="missing"/>',
            IssueCode.OPERATION_EXECUTION_FAILED,
        ),
    ],
)
def test_real_bounded_run_keeps_owner_identity_without_native_values(tmp_path, monkeypatch, body, issue):
    from datamimic_ce.authoring.domain.requests import RunRequest as AuthoringRunRequest

    monkeypatch.setenv("AUDIT_ERROR_TOKEN", SENTINEL)
    (tmp_path / "values.wgt.csv").write_text("a|1\nb|2\n")
    result = create_authoring_application(tmp_path).run(
        AuthoringRunRequest(
            xml=f'<setup rngSeed="7">{body}</setup>',
            allow_side_effects=True,
        )
    )
    assert not result.ok
    assert result.diagnostics[0].ce_error.issue_code is issue
    assert result.diagnostics[0].remediation
    assert SENTINEL not in result.model_dump_json()
