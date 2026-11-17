import os

import pytest


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """CI splits a long parametrized scenario test over runners: SCENARIO_SHARD=<index>/<count> keeps every count-th item."""
    shard = os.environ.get("SCENARIO_SHARD")
    if not shard:
        return
    index, count = (int(part) for part in shard.split("/"))
    kept = items[index::count]
    config.hook.pytest_deselected(items=[item for item in items if item not in kept])
    items[:] = kept
