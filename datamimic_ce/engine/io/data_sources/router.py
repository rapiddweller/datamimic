"""Route scalar source requests to IO-owned readers and row selectors."""

import logging
from collections import Counter
from collections.abc import Iterable
from contextvars import ContextVar, Token
from pathlib import Path
from types import TracebackType
from typing import TypeVar

from datamimic_ce.engine.dsl.vocabulary.constants.data_type_constants import DATA_TYPE_DICT, DATA_TYPE_LIST
from datamimic_ce.engine.dsl.vocabulary.constants.element_constants import EL_GENERATE, EL_NESTED_KEY
from datamimic_ce.engine.dsl.vocabulary.enums.distribution_enums import SourceDistribution
from datamimic_ce.engine.dsl.vocabulary.source_capabilities import (
    SourceFileFormat,
    source_file_format,
    source_file_format_for,
)
from datamimic_ce.engine.io.clients.client import RegisteredClient
from datamimic_ce.engine.io.clients.operations import (
    database_count_query_length,
    database_count_table_length,
    database_get_by_page_with_query,
    database_get_by_page_with_type,
    database_get_random_rows_by_columns,
    is_mongodb_client,
    is_rdbms_client,
    mongodb_count_collection,
    rdbms_count_source_query,
)
from datamimic_ce.engine.io.contracts import DataSourcePagination, MemstoreSource
from datamimic_ce.engine.io.data_sources.boundary.entities import resolve_source_collection, resolve_source_entity
from datamimic_ce.engine.io.data_sources.boundary.models import (
    CountSourceRequest,
    GenerateFileSource,
    GenerateFileSourceRequest,
)
from datamimic_ce.engine.io.data_sources.selection import get_distributed_data, get_unique_data, select_rows
from datamimic_ce.engine.io.files.readers import FileUtil, JsonValue, load_source_rows, weighted_csv_has_header
from datamimic_ce.errors import DescriptorLocation, IssueCode, OperationError, invalid_source_error, task_config_error
from datamimic_ce.randomness import RandomSource

logger = logging.getLogger("DATAMIMIC")
T = TypeVar("T")


_source_accesses: ContextVar[Counter[str] | None] = ContextVar("source_accesses", default=None)


class SourceAccessCapture:
    """Collect routed read requests for one execution, without resource locators."""

    def __init__(self) -> None:
        self._counts: Counter[str] = Counter()
        self._token: Token[Counter[str] | None] | None = None

    def __enter__(self) -> "SourceAccessCapture":
        if self._token is not None:
            raise RuntimeError("Source access capture is already active")
        self._counts.clear()
        self._token = _source_accesses.set(self._counts)
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None
    ) -> None:
        if self._token is not None:
            _source_accesses.reset(self._token)
            self._token = None

    def snapshot(self) -> tuple[tuple[str, int], ...]:
        return tuple(sorted(self._counts.items()))


def record_source_access(source_type: str) -> None:
    counts = _source_accesses.get()
    if counts is not None:
        counts[source_type] += 1


def count_source(
    request: CountSourceRequest,
    memstore: MemstoreSource | None,
    client: RegisteredClient | None,
) -> int | None:
    """Count a source in historical file, memstore, then client precedence."""
    source_format = source_file_format_for(request.element, request.source, request.source_type)
    if source_format is SourceFileFormat.DBUNIT_XML:
        entity = resolve_source_entity(request.source_entity, request.source_type, request.name)
        return len(FileUtil.read_dbunit_to_dict_list(request.descriptor_dir / request.source, entity))
    if source_format is SourceFileFormat.WEIGHTED_CSV:
        return len(
            FileUtil.read_weight_csv(
                request.descriptor_dir / request.source, request.separator or request.default_separator
            )
        )
    if source_format is not None:
        return len(
            load_source_rows(
                request.descriptor_dir / request.source,
                request.separator or request.default_separator,
                source_format,
            )
        )
    if memstore is not None:
        return memstore.get_data_len_by_type(
            resolve_source_entity(request.source_entity, request.source_type, request.name)
        )
    if client is None:
        logger.warning(f"Data source '{request.source}' is not supported for length calculation")
        return None

    selector = request.selector
    iteration_selector = request.iteration_selector
    if is_rdbms_client(client):
        if selector is not None:
            return rdbms_count_source_query(client, selector, request.source, "selector")
        if iteration_selector is not None:
            return rdbms_count_source_query(client, iteration_selector, request.source, "iterationSelector")
        if request.source_entity is not None or request.source_type is not None:
            entity = resolve_source_entity(request.source_entity, request.source_type, request.name)
            try:
                return database_count_table_length(client, entity)
            except OperationError as error:
                if error.location is None:
                    error.location = DescriptorLocation(
                        request.element, attribute="sourceEntity" if request.source_entity is not None else "type"
                    )
                raise
        return 0

    if is_mongodb_client(client):
        if selector is not None:
            try:
                return database_count_query_length(client, selector)
            except ValueError:
                return None
        collection = resolve_source_collection(request.source_entity, request.source_type)
        if collection is not None:
            try:
                return mongodb_count_collection(client, collection)
            except ValueError:
                return None
        if iteration_selector is not None:
            try:
                return database_count_query_length(client, iteration_selector)
            except ValueError:
                logger.error(
                    f"Cannot get length of database source '{request.source}' "
                    f"with iterationSelector '{iteration_selector}'"
                )
                return None
        raise ValueError("MongoDB source requires at least attribute 'type', 'selector' or 'iterationSelector'")

    raise invalid_source_error(code=IssueCode.SOURCE_CLIENT_UNSUPPORTED, client_type=type(client).__name__)


def read_generate_file_source(request: GenerateFileSourceRequest) -> GenerateFileSource | None:
    """Classify and read a <generate> file source, or return None for a non-file source."""
    file_path = request.descriptor_dir / request.source
    file_format = source_file_format_for(EL_GENERATE, request.source)
    if source_file_format(request.source) is SourceFileFormat.WEIGHTED_CSV and not weighted_csv_has_header(
        file_path, request.separator
    ):
        raise invalid_source_error(
            code=IssueCode.SOURCE_INVALID_CSV,
            name=Path(request.source).name,
            location=DescriptorLocation(EL_GENERATE, attribute="source"),
            guidance=(
                "A headerless weighted .wgt.csv source is supported by <key source=...> and <variable source=...>. "
                "Add a header row to read it as plain unweighted CSV at <generate>."
            ),
        )
    if file_format is None:
        return None

    record_source_access(f"file_{file_format.name.lower()}")
    rows: list[dict]
    if file_format is SourceFileFormat.DBUNIT_XML:
        rows = FileUtil.read_dbunit_to_dict_list(file_path, request.source_entity or request.name)[request.offset :]
    else:
        pagination = (
            DataSourcePagination(request.start_idx, request.end_idx - request.start_idx)
            if request.start_idx is not None and request.end_idx is not None
            else None
        )
        loaded: Iterable[dict] = load_source_rows(
            file_path, request.separator if file_format is SourceFileFormat.CSV else ",", file_format
        )
        rows = select_rows(
            loaded,
            pagination,
            False if request.cyclic is None else request.cyclic,
            request.offset,
        )
    return GenerateFileSource(file_format, rows)


def read_generate_database_source(
    client: RegisteredClient,
    selector: str | None,
    entity: str,
    collection: str | None,
    pagination: DataSourcePagination | None,
    has_upsert_target: bool,
) -> list[dict[str, object]]:
    """Read one resolved database source for a <generate> statement."""
    if is_mongodb_client(client):
        record_source_access("mongodb")
        if selector is not None:
            rows = database_get_by_page_with_query(client, selector, pagination)
        elif collection is not None:
            rows = database_get_by_page_with_type(client, collection, pagination)
        else:
            raise ValueError(
                "MongoDB source requires at least attribute 'sourceEntity', 'type', 'selector' or 'iterationSelector'"
            )
        if not rows and has_upsert_target:
            return [{}]
        return rows
    if is_rdbms_client(client):
        record_source_access("database")
        if selector is not None:
            return database_get_by_page_with_query(client, selector, pagination)
        return database_get_by_page_with_type(client, entity, pagination)
    raise invalid_source_error(code=IssueCode.SOURCE_CLIENT_UNSUPPORTED, client_type=type(client).__name__)


def read_generate_memstore_source(
    memstore: MemstoreSource,
    entity: str | None,
    pagination: DataSourcePagination | None,
    cyclic: bool | None,
) -> list[dict[str, object]]:
    """Read and select one <generate> pool from raw memstore rows."""
    record_source_access("memstore")
    return select_rows(memstore.get_data_by_type(entity), pagination, bool(cyclic))


def read_nested_key_source(
    descriptor_dir: Path,
    source_expression: str,
    source: str,
    source_type: str | None,
    source_entity: str | None,
    name: str | None,
    separator: str | None,
    default_separator: str,
    cyclic: bool | None,
    memstore: MemstoreSource | None,
) -> list[dict[str, str]] | list[JsonValue] | dict[str, JsonValue] | list[dict[str, object]]:
    """Read a resolved nested-key source without carrying DSL statements or context."""
    source_format = source_file_format_for(EL_NESTED_KEY, source, source_type)
    if source_format is not None:
        record_source_access(f"file_{source_format.name.lower()}")
    elif memstore is not None:
        record_source_access("memstore")
    if source_type == DATA_TYPE_LIST:
        if source_format is SourceFileFormat.CSV:
            return FileUtil.read_csv_to_dict_list(descriptor_dir / source, separator or default_separator)
        if source_format is SourceFileFormat.JSON:
            return FileUtil.read_json_to_list(descriptor_dir / source)
        if memstore is not None:
            return select_rows(
                memstore.get_data_by_type(resolve_source_entity(source_entity, source_type, name)),
                None,
                bool(cyclic),
            )
        raise invalid_source_error(code=IssueCode.TASK_NESTEDKEY_INVALID_SOURCE, source=source, name=name)

    if source_type == DATA_TYPE_DICT:
        if source_format is SourceFileFormat.JSON:
            return FileUtil.read_json_to_dict(descriptor_dir / source)
        raise invalid_source_error(code=IssueCode.TASK_NESTEDKEY_DICT_SOURCE_UNSUPPORTED, source=source, name=name)

    if memstore is not None:
        return select_rows(
            memstore.get_data_by_type(resolve_source_entity(source_entity, source_type, name)), None, bool(cyclic)
        )
    raise invalid_source_error(code=IssueCode.TASK_NESTEDKEY_SOURCE_UNSUPPORTED, source=source_expression, name=name)


def window_nested_key_rows(data: list[T], count: int | None, cyclic: bool | None) -> list[T]:
    """Select the rows for one nested-key execution."""
    size = len(data) if count is None else count if cyclic else min(count, len(data))
    return select_rows(data=data, pagination=DataSourcePagination(0, size), cyclic=bool(cyclic))


def read_reference_rows(
    client: RegisteredClient | None,
    source: str,
    source_type: str,
    source_keys: list[str],
    targets: list[str],
    name: str | None,
) -> list[dict[str, object]]:
    """Fetch and map the stable database row pool for one reference."""
    if not (is_rdbms_client(client) or is_mongodb_client(client)):
        raise task_config_error(code=IssueCode.TASK_REFERENCE_UNSUPPORTED_SOURCE, name=name)
    record_source_access("mongodb" if is_mongodb_client(client) else "database")
    rows = database_get_random_rows_by_columns(client, source_type, source_keys)
    if not rows:
        raise task_config_error(code=IssueCode.TASK_REFERENCE_NO_DATA, name=name)
    return [dict(zip(targets, row, strict=True)) for row in rows]


def select_reference_rows(
    records: list[T],
    pagination: DataSourcePagination | None,
    cyclic: bool | None,
    distribution: SourceDistribution,
    distribution_explicit: bool,
    unique: bool | None,
    seed: int,
    label: str,
    rng: RandomSource | None,
    default_cyclic_ordered: bool | None,
) -> list[T]:
    """Apply reference uniqueness, distribution, or ordinary runtime RNG selection."""
    if unique:
        return get_unique_data(records, pagination, seed, label)
    if distribution is SourceDistribution.ORDERED or default_cyclic_ordered:
        return _ordered_reference_rows(records, pagination, cyclic, label)
    if (distribution_explicit and distribution is not SourceDistribution.RANDOM) or cyclic:
        return get_distributed_data(records, pagination, cyclic, seed, distribution)

    size = pagination.limit if pagination is not None else 1
    if size <= 0:
        return []
    if rng is None:
        raise TypeError("Random source is required for positive random reference selection")
    return [rng.choice(records) for _ in range(size)]


def _ordered_reference_rows(
    records: list[T],
    pagination: DataSourcePagination | None,
    cyclic: bool | None,
    label: str,
) -> list[T]:
    if pagination is None:
        return records
    start = pagination.skip
    size = pagination.limit
    if cyclic:
        return [records[(start + index) % len(records)] for index in range(size)]
    if start + size > len(records):
        raise task_config_error(code=IssueCode.TASK_REFERENCE_ORDERED_EXHAUSTED, name=label, count=len(records))
    return records[start : start + size]


__all__ = [
    "SourceAccessCapture",
    "record_source_access",
    "count_source",
    "read_generate_file_source",
    "read_generate_database_source",
    "read_generate_memstore_source",
    "read_nested_key_source",
    "read_reference_rows",
    "select_reference_rows",
    "window_nested_key_rows",
]
