from pathlib import Path

import pytest

from datamimic_ce.errors import IssueCode, TaskConfigError
from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest

_DIR = Path(__file__).resolve().parent


def _run(filename: str):
    engine = DataMimicTest(test_dir=_DIR, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()


def test_assert_holds_per_record():
    rows = _run("assert_holds.xml")["g"]
    assert len(rows) == 20
    assert all(18 <= r["age"] <= 65 for r in rows)


def test_assert_violation_keeps_explicit_message_without_dumping_record():
    with pytest.raises(Exception, match=r"idx 3 is forbidden") as exc:
        _run("assert_violated.xml")
    assert exc.value.issue_code is IssueCode.TASK_ASSERT_FAILED
    assert "configured condition" in str(exc.value)
    assert "'idx': 3" not in str(exc.value)


def test_assert_setup_level_holds():
    rows = _run("assert_setup_level.xml")["g"]
    assert [r["v"] for r in rows] == [42, 42, 42]


def test_assert_setup_level_violation_fails():
    with pytest.raises(Exception, match=r"setup invariant broken"):
        _run("assert_setup_violated.xml")


def test_assert_broken_expression_names_the_assert():
    with pytest.raises(TaskConfigError) as rejected:
        _run("assert_bad_expression.xml")
    assert rejected.value.issue_code is IssueCode.TASK_EXPRESSION_EVAL_FAILED
    assert rejected.value.location.element_tag == "assert"
    assert rejected.value.location.attribute == "condition"
    assert type(rejected.value.__cause__) is NameError
    assert rejected.value.__cause__.name == "ixd"
