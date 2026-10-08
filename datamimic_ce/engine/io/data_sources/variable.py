"""IO operations for variable source reads."""

from collections.abc import Iterable

from datamimic_ce.engine.dsl.vocabulary.constants.element_constants import EL_VARIABLE
from datamimic_ce.engine.dsl.vocabulary.source_capabilities import SourceFileFormat, source_file_format_for
from datamimic_ce.engine.io.clients.client import RegisteredClient
from datamimic_ce.engine.io.clients.operations import (
    database_count_query_length,
    database_get_by_page_with_query,
    database_get_by_page_with_type,
    is_database_client,
)
from datamimic_ce.engine.io.contracts import DataSourcePagination, MemstoreSource
from datamimic_ce.engine.io.data_sources.boundary.entities import resolve_source_entity
from datamimic_ce.engine.io.data_sources.boundary.models import VariableSourceRequest
from datamimic_ce.engine.io.data_sources.selection import select_row_iterator, select_rows
from datamimic_ce.engine.io.files.readers import FileUtil


def read_variable_query(
    client: RegisteredClient,
    rendered_selector: str,
    pagination: DataSourcePagination | None,
    *,
    full_pool: bool,
    cached_length: int | None,
    cyclic: bool,
) -> Iterable[object]:
    """Read a selector-backed variable pool or its requested page."""
    if full_pool:
        return database_get_by_page_with_query(client, rendered_selector)

    length = cached_length
    if length is None:
        length = database_count_query_length(client, rendered_selector)
    if pagination is None or (cyclic and (pagination.limit > length or pagination.skip + pagination.limit > length)):
        rows = database_get_by_page_with_query(
            client, rendered_selector, DataSourcePagination(skip=0, limit=length)
        )
        return select_rows(rows, pagination, cyclic=cyclic)
    return database_get_by_page_with_query(client, rendered_selector, pagination)


def read_variable_source(
    request: VariableSourceRequest,
    client: RegisteredClient | None,
    memstore: MemstoreSource | None,
    pagination: DataSourcePagination | None,
) -> Iterable[object] | None:
    """Read one resolved file, database, or memstore variable source."""
    source_format = source_file_format_for(EL_VARIABLE, request.source)
    if source_format is not None:
        path = request.descriptor_dir / request.source
        data: Iterable[object]
        if source_format is SourceFileFormat.CSV:
            data = FileUtil.read_csv_to_dict_list(path, request.separator)
        elif source_format is SourceFileFormat.XLSX:
            data = FileUtil.read_xlsx_to_dict_list(path)
        elif source_format is SourceFileFormat.FIXED_WIDTH:
            data = FileUtil.read_fixed_width_to_dict_list(path)
        elif source_format is SourceFileFormat.JSON:
            data = FileUtil.read_json_to_list(path)
        else:
            raise ValueError(f"Unsupported <variable> source format: {source_format.value}")
        if not request.materialize_full_pool:
            return select_row_iterator(data, pagination, request.cyclic)
        return data

    if client is not None:
        if not is_database_client(client):
            raise ValueError(f"Cannot get data from source '{request.source}' of <variable> '{request.name}'")
        product_type = resolve_source_entity(request.source_entity, request.source_type, request.name)
        if product_type is None:
            return None
        if request.materialize_full_pool:
            return database_get_by_page_with_type(client, product_type)
        if request.cyclic:
            return select_rows(database_get_by_page_with_type(client, product_type), pagination, cyclic=True)
        return database_get_by_page_with_type(client, product_type, pagination)

    if memstore is not None:
        product_type = resolve_source_entity(request.source_entity, request.source_type, request.name)
        if request.materialize_full_pool:
            return memstore.get_all_data_by_type(product_type)
        return select_rows(memstore.get_data_by_type(product_type), pagination, request.cyclic)

    raise ValueError(f"Cannot find memstore '{request.source}' for <variable> '{request.name}'")


__all__ = ["VariableSourceRequest", "read_variable_query", "read_variable_source"]
