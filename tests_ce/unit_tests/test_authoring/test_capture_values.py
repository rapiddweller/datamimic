from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

import pytest


def test_capture_data_keeps_native_passive_values_and_shared_acyclic_containers():
    from datamimic_ce.authoring.domain.capture import validate_capture_values
    shared = [Decimal("1.20"), datetime(2026, 1, 1, tzinfo=timezone.utc), UUID(int=0)]
    validate_capture_values({"rows": [{"a": shared, "b": shared}]})


def test_cyclic_capture_is_rejected_before_consumers():
    from datamimic_ce.authoring.domain.capture import validate_capture_values
    row = {}
    row["self"] = row
    with pytest.raises(ValueError, match="cyclic"):
        validate_capture_values({"rows": [row]})


@pytest.mark.parametrize("value", [float("nan"), float("inf"), object(), {1: "non-string-key"}])
def test_non_passive_or_non_finite_capture_values_are_rejected(value):
    from datamimic_ce.authoring.domain.capture import validate_capture_values
    with pytest.raises(ValueError):
        validate_capture_values({"rows": [{"value": value}]})


def test_deep_capture_fails_closed_without_python_recursion_error():
    from datamimic_ce.authoring.domain.capture import validate_capture_values
    value = []
    for _ in range(100):
        value = [value]
    with pytest.raises(ValueError, match="depth"):
        validate_capture_values(value)
