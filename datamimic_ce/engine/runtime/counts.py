"""Count evaluation and range resolution for runtime tasks."""

from typing import SupportsIndex, SupportsInt

from datamimic_ce.domains.api import RandomSource
from datamimic_ce.engine.runtime.contexts.context import Context


def get_int_count(count: str | None, context: Context) -> int | None:
    if count is None:
        return None
    if count.isdigit():
        return int(count)
    value = context.evaluate_python_expression(count[1:-1])
    if isinstance(value, str | bytes | bytearray | SupportsInt | SupportsIndex):
        return int(value)
    raise TypeError(f"Count expression must evaluate to an integer-compatible value, got {type(value).__name__}")


def resolve_count(
    count: int | None, min_count: int | None, max_count: int | None, rng: RandomSource
) -> int | None:
    if count is not None:
        return count
    if min_count is not None and max_count is not None:
        return rng.randint(min_count, max_count)
    if max_count is not None:
        return rng.randint(max(0, max_count - 5), max_count)
    if min_count is not None:
        return rng.randint(min_count, min_count + 5)
    return None
