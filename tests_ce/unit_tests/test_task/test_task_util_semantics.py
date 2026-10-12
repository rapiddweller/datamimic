from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

import pytest

from datamimic_ce.domains.api import CustomConverter, RunSeed
from datamimic_ce.engine.dsl.vocabulary.constants.data_type_constants import (
    DATA_TYPE_BINARY,
    DATA_TYPE_BOOL,
    DATA_TYPE_DECIMAL,
    DATA_TYPE_FLOAT,
    DATA_TYPE_INT,
    DATA_TYPE_STRING,
)
from datamimic_ce.engine.runtime.scripting.evaluation import evaluate_condition_value, interpolate_variables
from datamimic_ce.engine.runtime.tasks.values.construction.converters import create_converter_list
from datamimic_ce.engine.runtime.tasks.values.construction.factory import generate_random_value_based_on_type


class _ExpressionContext:
    def __init__(self, values: dict[str, object]) -> None:
        self.values = values
        self.calls: list[str] = []

    def evaluate_python_expression(self, expression: str, local_namespace: dict[str, object] | None = None) -> object:
        self.calls.append(expression)
        return self.values[expression]


class _ContextAwareConverter(CustomConverter):
    def convert(self, value: object) -> object:
        return f"[{value}]"


class _ConverterContext:
    def __init__(self, seed: int) -> None:
        self.root = SimpleNamespace(
            run_seed=RunSeed.create(seed),
            get_dynamic_class=lambda name: {"ContextAwareConverter": _ContextAwareConverter}.get(name),
        )

    def evaluate_python_expression(self, expression: str, local_namespace: dict[str, object] | None = None) -> object:
        return eval(expression, local_namespace or {}, {})  # noqa: S307 - converter constructor syntax under test


class _ScalarRng:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    def randint(self, minimum: int, maximum: int) -> int:
        self.calls.append(("randint", (minimum, maximum)))
        return {(0, 20): 2, (0, 100): 42, (1, 16): 3}[minimum, maximum]

    def choice(self, values: object) -> object:
        self.calls.append(("choice", values))
        return "x" if isinstance(values, str) else False

    def uniform(self, minimum: int, maximum: int) -> float:
        self.calls.append(("uniform", (minimum, maximum)))
        return 12.345

    def randbytes(self, length: int) -> bytes:
        self.calls.append(("randbytes", length))
        return b"xyz"


def test_condition_evaluation_preserves_empty_boolean_and_invalid_rules() -> None:
    context = _ExpressionContext({"truth": True, "falsehood": False, "number": 1})

    assert evaluate_condition_value(context, "key", None) is True
    assert evaluate_condition_value(context, "key", "") is True
    assert evaluate_condition_value(context, "key", "truth") is True
    assert evaluate_condition_value(context, "key", "falsehood") is False
    assert context.calls == ["truth", "falsehood"]
    with pytest.raises(
        ValueError,
        match="Evaluated value of condition script 'number' in element 'variable' is not valid boolean value",
    ):
        evaluate_condition_value(context, "variable", "number")


def test_selector_uses_statement_markers_before_root_defaults() -> None:
    context = _ExpressionContext({"root_name": "root", "local_name": "local"})
    context.root = SimpleNamespace(default_variable_prefix="<<", default_variable_suffix=">>")

    fallback_statement = SimpleNamespace(
        selector="where name=<<root_name>>", variable_prefix=None, variable_suffix=None
    )
    explicit_statement = SimpleNamespace(
        selector="where name=[[local_name]]", variable_prefix="[[", variable_suffix="]]"
    )

    fallback_prefix = fallback_statement.variable_prefix or context.root.default_variable_prefix
    fallback_suffix = fallback_statement.variable_suffix or context.root.default_variable_suffix
    explicit_prefix = explicit_statement.variable_prefix or context.root.default_variable_prefix
    explicit_suffix = explicit_statement.variable_suffix or context.root.default_variable_suffix
    fallback_selector = interpolate_variables(
        context, fallback_statement.selector, fallback_prefix, fallback_suffix
    )
    explicit_selector = interpolate_variables(
        context, explicit_statement.selector, explicit_prefix, explicit_suffix
    )
    assert fallback_selector == "where name=root"
    assert explicit_selector == "where name=local"


def test_scalar_factory_preserves_rng_calls_and_defaults() -> None:
    rng = _ScalarRng()

    assert generate_random_value_based_on_type(DATA_TYPE_STRING, rng=rng) == "xx"
    assert generate_random_value_based_on_type(DATA_TYPE_INT, rng=rng) == 42
    assert generate_random_value_based_on_type(DATA_TYPE_FLOAT, rng=rng) == 12.345
    assert generate_random_value_based_on_type(DATA_TYPE_DECIMAL, rng=rng) == Decimal("12.35")
    assert generate_random_value_based_on_type(DATA_TYPE_BOOL, rng=rng) is False
    assert generate_random_value_based_on_type(DATA_TYPE_BINARY, rng=rng) == b"xyz"
    assert rng.calls == [
        ("randint", (0, 20)),
        ("choice", "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"),
        ("choice", "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"),
        ("randint", (0, 100)),
        ("uniform", (0, 100)),
        ("uniform", (0, 100)),
        ("choice", (True, False)),
        ("randint", (1, 16)),
        ("randbytes", 3),
    ]


def test_converter_construction_preserves_order_dynamic_context_and_seeded_hash_key() -> None:
    context = _ConverterContext(seed=23)
    converters = create_converter_list(context, "LowerCase;Append('_done');ContextAwareConverter")

    value: object = "ABC"
    for converter in converters:
        value = converter.convert(value)
    assert value == "[abc_done]"
    assert converters[2]._ctx is context

    def token(seed: int) -> str:
        converter = create_converter_list(_ConverterContext(seed), "Hash('sha256', 'hex')")[0]
        return converter.convert("account-7")

    assert token(23) == token(23)
    assert token(23) != token(24)

    mask_converters = create_converter_list(context, "Mask('#');MiddleMask(1,1,'#')")
    assert mask_converters[0].convert("abcd") == "####"
    assert mask_converters[1].convert("abcd") == "a##d"
    with pytest.raises(ValueError):
        create_converter_list(context, "Mask(['#'])")
    with pytest.raises(ValueError):
        create_converter_list(context, "MiddleMask(1,1,b'#')")
