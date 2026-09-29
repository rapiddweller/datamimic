"""Shared minCount/maxCount validation for generate and nestedKey."""

import pytest
from pydantic import ValidationError

from datamimic_ce.engine.dsl.model.generation.generate_model import GenerateModel
from datamimic_ce.engine.dsl.model.values.structured.nested_key_model import NestedKeyModel


@pytest.mark.parametrize(
    ("model", "base"),
    [
        (GenerateModel, {"name": "items", "source": "items.csv"}),
        (NestedKeyModel, {"name": "items", "type": "list"}),
    ],
)
def test_min_max_count_numeric_strings_use_numeric_order(model, base):
    valid = model.model_validate({**base, "minCount": "9", "maxCount": "10"})
    assert (valid.min_count, valid.max_count) == (9, 10)

    with pytest.raises(ValidationError, match="must be less than or equal"):
        model.model_validate({**base, "minCount": "10", "maxCount": "9"})


@pytest.mark.parametrize(
    ("model", "base"),
    [
        (GenerateModel, {"name": "items", "source": "items.csv"}),
        (NestedKeyModel, {"name": "items", "type": "list"}),
    ],
)
@pytest.mark.parametrize("value", ["", "   ", "invalid"])
def test_min_max_count_malformed_strings_remain_validation_errors(model, base, value):
    with pytest.raises(ValidationError):
        model.model_validate({**base, "minCount": value, "maxCount": "10"})


@pytest.mark.parametrize(
    ("model", "base"),
    [
        (GenerateModel, {"name": "items", "source": "items.csv"}),
        (NestedKeyModel, {"name": "items", "type": "list"}),
    ],
)
def test_count_remains_mutually_exclusive_with_min_max_count(model, base):
    with pytest.raises(ValidationError, match="must not be defined"):
        model.model_validate({**base, "count": "1", "minCount": "1", "maxCount": "2"})


@pytest.mark.parametrize(
    ("model", "base"),
    [
        (GenerateModel, {"name": "items", "source": "items.csv"}),
        (NestedKeyModel, {"name": "items", "type": "list"}),
    ],
)
def test_decimal_looking_count_strings_do_not_bypass_ordering(model, base):
    with pytest.raises(ValidationError, match="must be less than or equal"):
        model.model_validate({**base, "minCount": "10.0", "maxCount": "9.0"})


@pytest.mark.parametrize(
    ("model", "base"),
    [
        (GenerateModel, {"name": "items", "source": "items.csv"}),
        (NestedKeyModel, {"name": "items", "type": "list"}),
    ],
)
def test_infinite_count_values_are_rejected(model, base):
    with pytest.raises(ValidationError):
        model.model_validate({**base, "minCount": float("inf"), "maxCount": 10})
