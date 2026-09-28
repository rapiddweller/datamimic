"""Runtime source operations for generate statements."""

from datamimic_ce.engine.dsl.api import (
    GenerateStatement,
)
from datamimic_ce.engine.dsl.vocabulary.source_capabilities import (
    SourceFileFormat,
)
from datamimic_ce.engine.io.api import (
    DataSourcePagination,
    GenerateFileSourceRequest,
    database_get_by_page_with_query,
    database_get_by_page_with_type,
    has_mongodb_upsert_target,
    is_mongodb_client,
    is_rdbms_client,
    read_generate_file_source,
    resolve_source_collection,
    resolve_source_entity,
)
from datamimic_ce.engine.runtime.contexts.context import SetupContext
from datamimic_ce.engine.runtime.contexts.geniter_context import GenIterContext
from datamimic_ce.engine.runtime.logging import logger
from datamimic_ce.engine.runtime.scripting.evaluation import evaluate_source_template, interpolate_variables


def load_generate_source(
    context: SetupContext | GenIterContext,
    stmt: GenerateStatement,
    source: str | None,
    separator: str,
    source_scripted: bool,
    start_idx: int | None,
    end_idx: int | None,
    pagination: DataSourcePagination | None,
) -> tuple[list[dict], bool]:
    """Resolve one generate source; IO owns file reads and their row windows."""
    build_from_source = True
    source_data: object = []
    root = context.root
    prefix = stmt.variable_prefix or root.default_variable_prefix
    suffix = stmt.variable_suffix or root.default_variable_suffix
    file_source = (
        read_generate_file_source(
            GenerateFileSourceRequest(
                source,
                root.descriptor_dir,
                stmt.full_name,
                separator,
                stmt.cyclic,
                start_idx,
                end_idx,
                stmt.offset,
                resolve_source_entity(stmt.source_entity, stmt.type, stmt.name),
            )
        )
        if source is not None
        else None
    )

    if source is None:
        if stmt.script is None:
            build_from_source = False
        else:
            source_data = context.evaluate_python_expression(stmt.script)
    elif file_source is not None:
        source_data = file_source.rows
        if file_source.file_format is SourceFileFormat.CSV and source_scripted:
            evaluated_result = evaluate_source_template(root, source_data, prefix, suffix)
            source_data = evaluated_result if isinstance(evaluated_result, list) else [evaluated_result]
        elif file_source.file_format is SourceFileFormat.JSON and source_scripted:
            try:
                source_data = evaluate_source_template(root, source_data, prefix, suffix)
            except Exception as error:
                logger.debug(f"Failed to pre-evaluate source script for {stmt.full_name}: {error}")
        elif file_source.file_format is SourceFileFormat.XML and source_scripted:
            source_data = evaluate_source_template(context, source_data, prefix, suffix)
    elif root.memstore_manager.contain(source):
        if stmt.offset:
            raise ValueError(
                f"<generate> '{stmt.full_name}': offset= is only supported for file sources, not memstore '{source}'"
            )
        source_data = root.memstore_manager.get_memstore(source).get_data_by_type(
            resolve_source_entity(stmt.source_entity, stmt.type, stmt.name), pagination, stmt.cyclic
        )
    elif root.clients.get(source) is not None:
        if stmt.offset:
            raise ValueError(
                f"<generate> '{stmt.full_name}': offset= is only supported for file sources, "
                f"not database client '{source}' - use a selector with an SQL/Mongo skip instead"
            )
        client = root.clients[source]
        selector = interpolate_variables(root, stmt.selector or "", prefix, suffix)
        if is_mongodb_client(client):
            if stmt.selector:
                source_data = database_get_by_page_with_query(client, selector, pagination)
            elif (collection := resolve_source_collection(stmt.source_entity, stmt.type)) is not None:
                source_data = database_get_by_page_with_type(client, collection, pagination)
            else:
                raise ValueError(
                    "MongoDB source requires at least attribute 'sourceEntity', 'type', 'selector' "
                    "or 'iterationSelector'"
                )
            if not source_data and has_mongodb_upsert_target(stmt.targets, root.clients):
                source_data = [{}]
        elif is_rdbms_client(client):
            if stmt.selector:
                source_data = database_get_by_page_with_query(client, selector, pagination)
            else:
                entity = resolve_source_entity(stmt.source_entity, stmt.type, stmt.name)
                source_data = database_get_by_page_with_type(client, entity, pagination)
        else:
            raise ValueError(f"Cannot load data from client: {type(client).__name__}")
    else:
        raise ValueError(f"cannot find data source {source} for iterate task")

    rows = source_data if isinstance(source_data, list) else [source_data]
    return rows, build_from_source
