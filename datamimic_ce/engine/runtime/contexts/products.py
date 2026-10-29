"""Generated rows and the actual nested export executions for one worker/page."""

from __future__ import annotations

from dataclasses import dataclass, field

from datamimic_ce.engine.dsl.api import GenerateStatement
from datamimic_ce.engine.io.api import resolve_target_entity
from datamimic_ce.errors import IssueCode, task_config_error


@dataclass
class TotalRowBudget:
    """One runtime run's shared allowance for captured product rows."""

    limit: int
    used: int = 0

    def reserve(self) -> None:
        if self.used >= self.limit:
            raise task_config_error(code=IssueCode.TASK_TOTAL_ROW_BUDGET_EXCEEDED, limit=self.limit)
        self.used += 1

    def release(self, rows: int) -> None:
        self.used -= rows


@dataclass(frozen=True)
class ExecutedExport:
    product_name: str
    export_uri: str | None
    targets: tuple[str, ...]

    @classmethod
    def from_statement(cls, stmt: GenerateStatement) -> ExecutedExport:
        return cls(
            resolve_target_entity(stmt.target_entity, None, stmt.name), stmt.export_uri, tuple(sorted(stmt.targets))
        )


@dataclass
class NestedExport:
    statement: GenerateStatement
    rows: list[dict[str, object]]
    children: list[NestedExport] = field(default_factory=list)


class GenerationResult(dict[str, list]):
    """Keep public product names while transporting execution metadata across workers."""

    def __init__(self) -> None:
        super().__init__()
        self.exports: dict[ExecutedExport, set[int]] = {}
        self.nested_exports: list[NestedExport] = []

    def record_export(self, statement: GenerateStatement, worker_id: int) -> None:
        self.exports.setdefault(ExecutedExport.from_statement(statement), set()).add(worker_id)

    def merge_exports(self, result: dict[str, list]) -> None:
        if isinstance(result, GenerationResult):
            for export, workers in result.exports.items():
                self.exports.setdefault(export, set()).update(workers)
