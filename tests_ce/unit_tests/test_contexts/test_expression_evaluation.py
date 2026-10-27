import copy
import datetime
import json
import sys
from pathlib import Path

import pytest
from faker import Faker

from datamimic_ce.domains.api import RunSeed
from datamimic_ce.engine.io.exporters.diagnostics.test_result_exporter import TestResultExporter
from datamimic_ce.engine.runtime.contexts.context import SetupContext
from datamimic_ce.engine.runtime.storage.memstore_manager import MemstoreManager
from datamimic_ce.errors import IssueCode, TaskConfigError
from datamimic_ce.errors.formatters import task_config_message


def _context(*, namespace: dict[str, object] | None = None, seeded: bool = False) -> SetupContext:
    return SetupContext(
        memstore_manager=MemstoreManager(),
        task_id="expression-evaluation-test",
        test_mode=True,
        test_result_exporter=TestResultExporter(),
        default_separator="|",
        default_locale="en",
        default_dataset="US",
        use_mp=False,
        descriptor_dir=Path("."),
        num_process=1,
        default_variable_prefix="__",
        default_variable_suffix="__",
        default_line_separator="\n",
        namespace=namespace,
        run_seed=RunSeed.create(7 if seeded else None),
    )


def test_expression_returns_scalars_and_normalizes_dotable_dicts_recursively() -> None:
    context = _context(namespace={"record": {"id": 4}, "items": [{"id": 5}]})

    assert context.evaluate_python_expression("40 + 2") == 42
    assert context.evaluate_python_expression("record") == {"id": 4}
    assert context.evaluate_python_expression("record.id") == 4
    result = context.evaluate_python_expression("[record, [record]]")
    assert result[0] == {"id": 4}
    assert type(result[1][0]) is dict
    assert result[1][0] == {"id": 4}
    assert isinstance(context.evaluate_python_expression("items[0]"), dict)


@pytest.mark.parametrize(
    ("expression", "message"),
    [
        ("len", "'configured expression' is an callable function, not a valid type (string, integer, float,...)"),
        ("math", "'configured expression' is an callable function, not a valid type (string, integer, float,...)"),
        ("fake", "'configured expression' is _SeededFaker function, not a valid type (string, integer, float,...)"),
        ("faker", "'configured expression' is Faker function, not a valid type (string, integer, float,...)"),
    ],
)
def test_expression_rejects_non_values(expression: str, message: str) -> None:
    context = _context(namespace={"faker": Faker()} if expression == "faker" else None, seeded=expression == "fake")

    with pytest.raises(ValueError) as exc:
        context.evaluate_python_expression(expression)

    assert type(exc.value) is TaskConfigError
    assert str(exc.value) == task_config_message(
        code=IssueCode.TASK_EXPRESSION_EVAL_FAILED, expr="configured expression", error=message
    )


@pytest.mark.parametrize(
    ("expression", "message", "cause_type"),
    [
        (
            "missing",
            "NameError: name 'missing' is not defined: "
            "check spelling, definition order and value shape; current-scope names can resolve bare, "
            "but existing outermost bare names win collisions; intermediate ancestor names need qualification; "
            "use this.name for the current scope, parent.name for the immediate enclosing record, "
            "or root.name for an outermost field when these aliases are available, or use a qualified scope path",
            NameError,
        ),
        (
            "record.missing",
            "AttributeError: no attribute 'missing': "
            "check spelling, definition order and value shape; current-scope names can resolve bare, "
            "but existing outermost bare names win collisions; intermediate ancestor names need qualification; "
            "use this.name for the current scope, parent.name for the immediate enclosing record, "
            "or root.name for an outermost field when these aliases are available, or use a qualified scope path",
            AttributeError,
        ),
        (
            "{'present': 1}['missing']",
            "KeyError: missing mapping key",
            KeyError,
        ),
        (
            "1 + 'x'",
            "Failed while evaluate 'configured expression': "
            "'configured expression' have undefined item or wrong structure",
            TypeError,
        ),
        (
            "1 +",
            "Evaluation error for expression 'configured expression': "
            "The expression may contain undefined elements, formatting errors, "
            "or unsupported parameter names. Ensure that boolean values and all parameter names "
            "(e.g., 'True' vs 'true') adhere to the required formats.",
            SyntaxError,
        ),
        (
            "int('x')",
            "ValueError",
            ValueError,
        ),
    ],
)
def test_expression_errors_keep_messages_and_causes(expression: str, message: str, cause_type: type[Exception]) -> None:
    context = _context(namespace={"record": {"id": 1}})

    with pytest.raises(ValueError) as exc:
        context.evaluate_python_expression(expression)

    assert type(exc.value) is TaskConfigError
    assert str(exc.value) == task_config_message(
        code=IssueCode.TASK_EXPRESSION_EVAL_FAILED, expr="configured expression", error=message
    )
    assert isinstance(exc.value.__cause__, cause_type)


def test_colon_names_are_rewritten_and_normalized() -> None:
    context = _context(namespace={"container": {"gc:CodeList": {"ColumnSet": {"id_value": 13}}}})

    assert context.evaluate_python_expression(r"container.gc:CodeList.ColumnSet.id_value") == 13


def test_colon_retry_failure_keeps_safe_guidance_and_native_cause() -> None:
    context = _context()

    with pytest.raises(ValueError) as exc:
        context.evaluate_python_expression(r"missing\:item.value")

    legacy_message = (
        "Evaluation error for expression 'configured expression': The expression may contain undefined items, "
        "improper structure, or case-sensitive issues (e.g., using 'true' instead of 'True'). "
        "Please double-check that all parameters and type notations are correct and supported."
    )
    assert type(exc.value) is TaskConfigError
    assert str(exc.value) == task_config_message(
        code=IssueCode.TASK_EXPRESSION_EVAL_FAILED, expr="configured expression", error=legacy_message
    )
    assert isinstance(exc.value.__cause__, NameError)


def test_seeded_expression_evaluation_does_not_draw_before_expression_needs_randomness() -> None:
    context = _context(seeded=True)
    expected_rng = copy.deepcopy(context.rng)
    initial_state = context.rng.getstate()

    assert context.evaluate_python_expression("1") == 1
    assert context.rng.getstate() == initial_state
    assert context.evaluate_python_expression("random.randint(1, 100)") == expected_rng.randint(1, 100)


def test_colon_retry_preserves_seeded_entropy_policy():
    context = _context(namespace={"container": {"gc:value": 1}}, seeded=True)
    with pytest.raises(TaskConfigError, match="'os.urandom' draws entropy") as caught:
        context.evaluate_python_expression("container.gc:value + os.urandom(1)")
    assert caught.value.issue_code is IssueCode.TASK_EXPRESSION_EVAL_FAILED
    assert caught.value.__cause__ is None


def test_colon_retry_preserves_frozen_domain_error_identity():
    from datamimic_ce.errors import DomainError, DomainErrorCode

    error = DomainError(DomainErrorCode.INVALID_REQUEST, "invalid", "repair", "/field", "hash")

    def refuse():
        raise error

    context = _context(namespace={"container": {"gc:refuse": refuse}})
    with pytest.raises(DomainError) as caught:
        context.evaluate_python_expression("container.gc:refuse()")
    assert caught.value is error


_REPLACED_DATETIME = (
    "the expression reads 'datetime', which a script, variable or field binds in place of the engine's 'datetime'"
)


@pytest.mark.parametrize(
    ("namespace", "expression", "hinted"),
    [
        ({"datetime": datetime.datetime}, "datetime.date(2026, 3, 2)", True),
        ({"datetime": datetime.datetime}, "datetime.timedelta(days=1)", True),
        ({"json": json}, "json.loads(1)", False),
        ({"datetime": "retail"}, "datetime.upper() + missing_name", False),
        ({"datetime": datetime.datetime, "record": {"id": 1}}, "datetime.now() and record.nope", False),
    ],
    ids=["type_error", "attribute_error", "same_object", "unrelated_name_error", "attribute_on_another_name"],
)
def test_a_failing_expression_names_an_engine_name_that_a_script_replaces(
    namespace: dict[str, object], expression: str, hinted: bool
) -> None:
    """Python-only: a scenario negative asserts only text that is present, and one patch reaches only the first
    failing key; this test also proves the absent hint when the script binds the engine's own object, and when the
    failure is about another name than the replaced one (a legit field must not get "rename the field" advice)."""
    with pytest.raises(TaskConfigError) as exc:
        _context(namespace=namespace).evaluate_python_expression(expression)

    assert ("in place of the engine's" in str(exc.value)) is hinted
    if hinted:
        assert _REPLACED_DATETIME in str(exc.value)


def test_text_from_data_is_not_kept_in_the_compile_cache() -> None:
    """Python-only: retention is process memory, which no descriptor can observe. Data text is a value per row, so
    caching it holds every distinct text (1 MB here) for the process lifetime."""
    from datamimic_ce.engine.runtime.scripting import evaluation

    context = _context()
    big = "'" + "a" * 1_000_000 + "'"
    evaluation._compiled.cache_clear()

    assert len(context.evaluate_python_expression(big, text_from_data=True)) == 1_000_000
    assert evaluation._compiled.cache_info().currsize == 0
    context.evaluate_python_expression("40 + 2")
    assert evaluation._compiled.cache_info().currsize == 1


def test_an_assignment_in_a_generator_expression_does_not_reach_the_shared_engine_names() -> None:
    """Python-only: only an unseeded run shares one engine-name dict across evaluations, and every scenario sets
    rngSeed (a seeded run copies the dict per evaluation). A later generate must not read the name."""
    from datamimic_ce.engine.runtime.scripting.expression_globals import SAFE_GLOBALS

    context = _context()
    assert context.evaluate_python_expression("any((leaked := v * 100) for v in [2])") is True

    assert "leaked" not in SAFE_GLOBALS
    with pytest.raises(TaskConfigError, match="NameError: name 'leaked' is not defined"):
        context.evaluate_python_expression("leaked")


@pytest.mark.skipif(
    sys.version_info >= (3, 12),
    reason="3.12+ inlines comprehensions (PEP 709): there the field already won before #423, so no value changes",
)
def test_a_field_named_max_wins_inside_a_comprehension_on_python_3_11() -> None:
    """Python 3.11 value change of #423: a field `max` read in `[max(a, 2) for ...]` used the builtin and gave
    '[2, 3]'. The comprehension now sees the field, as the top level does, so the call fails and names the field."""
    with pytest.raises(TaskConfigError) as exc:
        _context(namespace={"max": 7}).evaluate_python_expression("str([max(a, 2) for a in [1, 3]])")

    assert isinstance(exc.value.__cause__, TypeError)
    assert "the expression reads 'max', which a script, variable or field binds in place of the engine's" in str(
        exc.value
    )
