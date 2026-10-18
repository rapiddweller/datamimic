from pathlib import Path

import pytest

from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest
from datamimic_ce.errors import IssueCode, TaskConfigError

_DIR = Path(__file__).resolve().parent


def _run(filename: str):
    engine = DataMimicTest(test_dir=_DIR, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()


def test_assert_holds_per_record():
    rows = _run("assert_holds.xml")["g"]
    assert len(rows) == 20
    assert all(18 <= r["age"] <= 65 for r in rows)


def test_assert_violation_fails_with_message_and_record():
    with pytest.raises(Exception, match=r"idx 3 is forbidden") as exc:
        _run("assert_violated.xml")
    assert "idx != 3" in str(exc.value)  # failing condition named
    assert "'idx': 3" in str(exc.value)  # offending record dumped


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
    assert "ixd == 1" in str(rejected.value) and "assert" in str(rejected.value)
    assert isinstance(rejected.value.__cause__, TaskConfigError)
    assert isinstance(rejected.value.__cause__.__cause__, NameError)
