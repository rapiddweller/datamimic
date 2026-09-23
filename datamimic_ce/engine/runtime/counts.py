"""Count evaluation and range resolution for runtime tasks."""

from random import Random

from datamimic_ce.engine.runtime.contexts.context import Context


def get_int_count(count: str | None, context: Context) -> int | None:
    if count is None:
        return None
    if count.isdigit():
        return int(count)
    return int(context.evaluate_python_expression(count[1:-1]))


def resolve_count(
    count: int | None, min_count: int | None, max_count: int | None, rng: Random
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
