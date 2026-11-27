"""<execute script="...">: the evaluated expression IS the code to run — the DSL-native way to
execute dynamically assembled statements (paired with <variable string="...__var__..."/>).
"""

from pathlib import Path

import pytest

from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest
from datamimic_ce.errors import IssueCode, ParserValidationError


def _run(project_dir: Path, filename: str) -> dict:
    engine = DataMimicTest(test_dir=project_dir, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()


def test_execute_script_runs_assembled_sql(project_dir):
    rows = _run(project_dir, "execute_script_sql.xml")["rows"]
    assert [(r["id"], r["note"]) for r in rows] == [(1, "a"), (2, "b")]


def test_execute_script_runs_assembled_python(project_dir):
    rows = _run(project_dir, "execute_script_python.xml")["g"]
    assert [r["v"] for r in rows] == [42, 42]


def test_execute_script_non_string_value_raises(project_dir):
    with pytest.raises(Exception, match=r"script.*must evaluate to a string|evaluate[sd]? to.*int"):
        _run(project_dir, "execute_script_non_string.xml")


def test_execute_script_plus_uri_is_a_parse_error(project_dir):
    from pydantic import ValidationError

    with pytest.raises(ParserValidationError) as rejected:
        _run(project_dir, "execute_script_and_uri.xml")
    assert rejected.value.issue_code is IssueCode.PARSER_VALIDATION_FAILED
    assert isinstance(rejected.value.__cause__, ValidationError)
    assert rejected.value.validation_errors


def test_execute_script_plus_inline_body_is_a_parse_error(project_dir):
    with pytest.raises(ParserValidationError) as rejected:
        _run(project_dir, "execute_script_and_body.xml")
    assert rejected.value.issue_code is IssueCode.PARSER_EXECUTE_INVALID_SOURCE
