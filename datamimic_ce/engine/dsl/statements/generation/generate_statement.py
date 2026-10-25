# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.engine.dsl.model.generation.generate_model import GenerateModel
from datamimic_ce.engine.dsl.model.generation.timeseries import TimeSeriesConfig
from datamimic_ce.engine.dsl.statements.base.composite_statement import CompositeStatement
from datamimic_ce.engine.dsl.statements.base.statement import Statement
from datamimic_ce.engine.dsl.statements.generation.targets import parse_consumer
from datamimic_ce.engine.dsl.vocabulary.enums.distribution_enums import SourceDistribution
from datamimic_ce.engine.dsl.vocabulary.enums.operation_enums import ExportOperation


class GenerateStatement(CompositeStatement):
    def __init__(self, model: GenerateModel, parent_stmt: Statement):
        name = model.name
        super().__init__(name, parent_stmt)
        self._count = model.count
        self._min_count = model.min_count
        self._max_count = model.max_count
        self._source = model.source
        self._cyclic = model.cyclic
        self._offset = model.offset
        self._unique = model.unique
        self._source_script = model.source_scripted
        self._type = model.type
        self._source_entity = model.source_entity
        self._target_entity = model.target_entity
        self._selector = model.selector
        self._separator = model.separator
        self._targets: set[str] = parse_consumer(model.target)
        self._page_size = model.page_size
        self._mp = model.multiprocessing
        self._export_uri = model.export_uri
        # Real type at the boundary (absent = RANDOM). <generate> accepts random/ordered/cumulated.
        self._distribution = SourceDistribution.coerce(model.distribution)
        self._variable_prefix = model.variable_prefix
        self._variable_suffix = model.variable_suffix
        self._converter = model.converter
        self._num_process = model.num_process
        self._script = model.script
        self._mp_platform = model.mp_platform
        self._start = model.start
        self._end = model.end
        self._interval = model.interval
        # Set only by bounded Authoring execution: runtime counts above it are refused, never truncated.
        self._bounded_count_limit: int | None = None

    @property
    def name(self) -> str:
        if self._name is None:
            raise ValueError("Error while parsing element <generate>: 'name' cannot be None")
        return self._name

    @property
    def full_name(self) -> str:
        if self._full_name is None:
            raise ValueError("Error while parsing element <generate>: 'full_name' cannot be None")
        return self._full_name

    @property
    def count(self) -> str | None:
        return self._count

    @count.setter
    def count(self, value: str | None) -> None:
        self._count = value

    @property
    def unique(self) -> bool | None:
        return self._unique

    @property
    def min_count(self) -> int | None:
        return self._min_count

    @property
    def max_count(self) -> int | None:
        return self._max_count

    @property
    def source(self) -> str | None:
        return self._source

    @property
    def cyclic(self) -> bool | None:
        return self._cyclic

    @property
    def offset(self) -> int:
        """Rows to skip at the start of the source; 0 when not set."""
        return self._offset or 0

    @property
    def source_script(self) -> bool | None:
        return self._source_script

    @property
    def type(self) -> str | None:
        return self._type

    @property
    def source_entity(self) -> str | None:
        return self._source_entity

    @property
    def client_operations(self) -> tuple[tuple[str, ExportOperation], ...]:
        """``(clientId, operation)`` of each target that names a client operation (``db.delete``), by target."""
        parsed = (ExportOperation.from_target(target) for target in sorted(self._targets))
        return tuple(item for item in parsed if item is not None)

    @property
    def is_statement_operation(self) -> bool:
        """Whether a target is a source-free ``clear`` or ``drop``, which runs once instead of generating rows."""
        return any(operation.is_statement_operation for _, operation in self.client_operations)

    @property
    def operation_target(self) -> str:
        """The clear or drop targets as written for a message, for example ``db.clear``."""
        return ", ".join(f"{client}.{operation.value}" for client, operation in self.client_operations)

    @property
    def delete_target(self) -> str | None:
        """The delete targets as written for a message, for example ``db.delete``; None without one."""
        names = [
            f"{client}.delete" for client, operation in self.client_operations if operation is ExportOperation.DELETE
        ]
        return ", ".join(names) or None

    def delete_intent_problem(self, *, source_is_database: bool) -> tuple[str, str] | None:
        """``(reason, migration)`` when a ``delete`` would remove everything its database source reads, None otherwise.

        A file source lists the rows to delete and a generated row deletes by its own keys: neither needs a selector."""
        if self.delete_target is None or not source_is_database or self._selector is not None:
            return None
        return (
            "delete reads a database source without a selector, so it removes every row the source returns",
            "add a selector that selects the rows to delete, or use clientId.clear or clientId.drop to remove all",
        )

    def operation_intent_problem(self, *, nested: bool) -> tuple[str, str] | None:
        """``(reason, migration)`` of the first rule a clear or drop breaks (BC-4.0-016), None for a valid one-time
        statement. The runtime and bounded authoring run this same check."""
        if nested:
            return (
                "clear and drop are root-only operations and cannot run in a nested context",
                "move the operation to the root <setup> scope",
            )
        if not self._target_entity or not self._target_entity.strip():
            return (
                "clear and drop require explicit targetEntity",
                "set targetEntity to the table or collection to mutate",
            )
        present = {
            "children": bool(self.sub_statements),
            "count": any(value is not None for value in (self._count, self._min_count, self._max_count)),
            "interval": any(value is not None for value in (self._start, self._end, self._interval)),
            "otherTargets": len(self._targets) > 1,
            "script": self._script is not None,
            "selector": self._selector is not None,
            "source": self._source is not None,
            "sourceEntity": self._source_entity is not None,
        }
        forbidden = sorted(name for name, found in present.items() if found)
        if forbidden:
            return (
                f"clear and drop are source-free one-time operations; forbidden attributes: {', '.join(forbidden)}",
                "remove source, selectors, count, keys/children, scripts, and additional targets",
            )
        return None

    @property
    def target_entity(self) -> str | None:
        return self._target_entity

    @property
    def selector(self) -> str | None:
        return self._selector

    @property
    def separator(self) -> str | None:
        return self._separator

    @property
    def targets(self) -> set[str]:
        return self._targets

    @targets.setter
    def targets(self, value: set[str]) -> None:
        self._targets = value

    @property
    def page_size(self) -> int | None:
        return self._page_size

    @property
    def multiprocessing(self) -> bool | None:
        return self._mp

    @property
    def export_uri(self) -> str | None:
        return self._export_uri

    @property
    def distribution(self) -> SourceDistribution:
        return self._distribution

    @property
    def variable_prefix(self) -> str | None:
        return self._variable_prefix

    @property
    def variable_suffix(self) -> str | None:
        return self._variable_suffix

    @property
    def converter(self) -> str | None:
        return self._converter

    @property
    def num_process(self) -> int | None:
        return self._num_process

    @num_process.setter
    def num_process(self, value: int | None) -> None:
        self._num_process = value

    @property
    def script(self) -> str | None:
        return self._script

    @property
    def mp_platform(self) -> str | None:
        return self._mp_platform

    @property
    def start(self) -> str | None:
        return self._start

    @property
    def end(self) -> str | None:
        return self._end

    @property
    def interval(self) -> str | None:
        return self._interval

    def get_time_series_config(self) -> TimeSeriesConfig | None:
        """Parsed ``start``/``end``/``interval``; ``None`` when not in time-series mode.

        Callers branch on the result instead of inspecting ``interval`` directly,
        so the predicate and the parsing live in one place.
        """
        if self._interval is None:
            return None
        # GenerateModel validator guarantees start and end are non-None when interval is.
        assert self._start is not None and self._end is not None
        return TimeSeriesConfig.parse(self._start, self._end, self._interval)

    @property
    def bounded_count_limit(self) -> int | None:
        return self._bounded_count_limit

    @bounded_count_limit.setter
    def bounded_count_limit(self, value: int | None) -> None:
        self._bounded_count_limit = value
