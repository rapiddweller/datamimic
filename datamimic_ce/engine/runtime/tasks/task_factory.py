"""Statement-to-task dispatch registry, populated by the tasks package."""

from __future__ import annotations

from functools import singledispatch
from typing import TYPE_CHECKING

from datamimic_ce.engine.dsl.api import Statement

if TYPE_CHECKING:
    from datamimic_ce.engine.io.api import DataSourcePagination
    from datamimic_ce.engine.runtime.contexts.setup_context import SetupContext
    from datamimic_ce.engine.runtime.tasks.task import Task


@singledispatch
def create_task(
    statement: Statement,
    context: SetupContext,
    pagination: DataSourcePagination | None = None,
) -> Task:
    raise ValueError(f"Cannot create a task for statement {statement.__class__.__name__}")
