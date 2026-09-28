import copy
from pathlib import Path

import pytest
from faker import Faker

from datamimic_ce.domains.api import RunSeed
from datamimic_ce.engine.io.exporters.diagnostics.test_result_exporter import TestResultExporter
from datamimic_ce.engine.runtime.contexts.context import SetupContext
from datamimic_ce.engine.runtime.scripting.evaluation import DotableDict
from datamimic_ce.engine.runtime.storage.memstore_manager import MemstoreManager


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


def test_expression_returns_scalars_and_normalizes_dotable_dicts_shallowly() -> None:
    context = _context(namespace={"record": {"id": 4}, "items": [{"id": 5}]})

    assert context.evaluate_python_expression("40 + 2") == 42
    assert context.evaluate_python_expression("record") == {"id": 4}
    assert context.evaluate_python_expression("record.id") == 4
    result = context.evaluate_python_expression("[record, [record]]")
    assert result[0] == {"id": 4}
    assert isinstance(result[1][0], DotableDict)
    assert result[1][0].id == 4
    assert isinstance(context.evaluate_python_expression("items[0]"), dict)


@pytest.mark.parametrize(
    ("expression", "message"),
    [
        ("len", "'len' is an callable function, not a valid type (string, integer, float,...)"),
        ("math", "'math' is an callable function, not a valid type (string, integer, float,...)"),
        ("fake", "'fake' is _SeededFaker function, not a valid type (string, integer, float,...)"),
        ("faker", "'faker' is Faker function, not a valid type (string, integer, float,...)"),
    ],
)
def test_expression_rejects_non_values(expression: str, message: str) -> None:
    context = _context(namespace={"faker": Faker()} if expression == "faker" else None, seeded=expression == "fake")

    with pytest.raises(ValueError) as exc:
        context.evaluate_python_expression(expression)

    assert str(exc.value) == f"Failed while evaluate '{expression}': {message}"
    assert isinstance(exc.value.__cause__, ValueError)


@pytest.mark.parametrize(
    ("expression", "message", "cause_type"),
    [
        (
            "missing",
            "Failed while evaluate 'missing': name 'missing' is not defined in this scope; "
            "a same-scope sibling resolves bare (or via this.) - check the name; "
            "an ANCESTOR scope's name needs parent./root., it does not resolve bare",
            NameError,
        ),
        (
            "record.missing",
            "Failed while evaluate 'record.missing': missing attribute 'missing'; "
            "a same-scope sibling resolves bare (or via this.) - check the name; "
            "an ANCESTOR scope's name needs parent./root., it does not resolve bare",
            AttributeError,
        ),
        (
            "{'present': 1}['missing']",
            "Failed while evaluate '{'present': 1}['missing']': missing key 'missing'",
            KeyError,
        ),
        (
            "1 + 'x'",
            "Failed while evaluate '1 + 'x'': '1 + 'x'' have undefined item or wrong structure",
            TypeError,
        ),
        (
            "1 +",
            "Evaluation error for expression '1 +': The expression may contain undefined elements, formatting errors, "
            "or unsupported parameter names. Ensure that boolean values and all parameter names "
            "(e.g., 'True' vs 'true') adhere to the required formats.",
            SyntaxError,
        ),
        (
            "int('x')",
            "Failed while evaluate 'int('x')': invalid literal for int() with base 10: 'x'",
            ValueError,
        ),
    ],
)
def test_expression_errors_keep_messages_and_causes(
    expression: str, message: str, cause_type: type[Exception]
) -> None:
    context = _context(namespace={"record": {"id": 1}})

    with pytest.raises(ValueError) as exc:
        context.evaluate_python_expression(expression)

    assert str(exc.value) == message
    assert isinstance(exc.value.__cause__, cause_type)


def test_colon_names_are_rewritten_and_normalized() -> None:
    context = _context(namespace={"container": {"gc:CodeList": {"ColumnSet": {"id_value": 13}}}})

    assert context.evaluate_python_expression(r"container.gc:CodeList.ColumnSet.id_value") == 13


def test_colon_retry_failure_keeps_its_legacy_message_and_cause() -> None:
    context = _context()

    with pytest.raises(ValueError) as exc:
        context.evaluate_python_expression(r"missing\:item.value")

    assert str(exc.value) == (
        "Evaluation error for expression 'missing:item.value': The expression may contain undefined items, "
        "improper structure, or case-sensitive issues (e.g., using 'true' instead of 'True'). "
        "Please double-check that all parameters and type notations are correct and supported."
    )
    assert isinstance(exc.value.__cause__, NameError)


def test_seeded_expression_evaluation_does_not_draw_before_expression_needs_randomness() -> None:
    context = _context(seeded=True)
    expected_rng = copy.deepcopy(context.rng)
    initial_state = context.rng.getstate()

    assert context.evaluate_python_expression("1") == 1
    assert context.rng.getstate() == initial_state
    assert context.evaluate_python_expression("random.randint(1, 100)") == expected_rng.randint(1, 100)
