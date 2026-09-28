"""Runtime source operations for generate statements."""

from datamimic_ce.engine.dsl.api import (
    EL_GENERATE,
    GenerateStatement,
)
from datamimic_ce.engine.dsl.vocabulary.source_capabilities import (
    SourceFileFormat,
    source_file_format,
    source_file_format_for,
)
from datamimic_ce.engine.io.api import (
    DataSourcePagination,
    DataSourceRegistry,
    FileUtil,
    database_get_by_page_with_query,
    database_get_by_page_with_type,
    has_mongodb_upsert_target,
    is_mongodb_client,
    is_rdbms_client,
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
    """Load one generate source; this is the sole generate routing and paging owner."""
    build_from_source = True
    source_data: object = []
    root = context.root
    prefix = stmt.variable_prefix or root.default_variable_prefix
    suffix = stmt.variable_suffix or root.default_variable_suffix

    if source is None:
        if stmt.script is None:
            build_from_source = False
        else:
            source_data = context.evaluate_python_expression(stmt.script)
    elif source_file_format(
        source
    ) is SourceFileFormat.WEIGHTED_CSV and not DataSourceRegistry._weighted_csv_has_header(
        root.descriptor_dir / source, separator
    ):
        raise ValueError(
            f"<generate> '{stmt.full_name}': source '{source}' is a headerless weighted "
            "value|weight file - not supported at <generate>-level (only <key source=...> "
            "applies '.wgt.csv' weights today; add a header row to read it as a plain, "
            "unweighted CSV instead)"
        )
    elif (source_format := source_file_format_for(EL_GENERATE, source)) is SourceFileFormat.CSV:
        source_data = DataSourceRegistry.load_csv_file(
            file_path=root.descriptor_dir / source,
            separator=separator,
            cyclic=stmt.cyclic,
            start_idx=start_idx,
            end_idx=end_idx,
            offset=stmt.offset,
        )
        # sourceScripted evaluates csv expressions after loading - kept at the router (the
        # caller decides source policy; the loader itself has no context to evaluate against).
        if source_scripted:
            evaluated_result = evaluate_source_template(root, source_data, prefix, suffix)
            source_data = evaluated_result if isinstance(evaluated_result, list) else [evaluated_result]
    elif source_format is SourceFileFormat.JSON:
        source_data = DataSourceRegistry.load_json_file(
            root.descriptor_dir / source, stmt.cyclic, start_idx, end_idx, offset=stmt.offset
        )
        if source_scripted:
            try:
                source_data = evaluate_source_template(root, source_data, prefix, suffix)
            except Exception as error:
                logger.debug(f"Failed to pre-evaluate source script for {stmt.full_name}: {error}")
    elif source_format is SourceFileFormat.XLSX:
        source_data = DataSourceRegistry.load_xlsx_file(
            root.descriptor_dir / source, stmt.cyclic, start_idx, end_idx, offset=stmt.offset
        )
    elif source_format is SourceFileFormat.FIXED_WIDTH:
        source_data = DataSourceRegistry.load_fixed_width_file(
            root.descriptor_dir / source, stmt.cyclic, start_idx, end_idx, offset=stmt.offset
        )
    elif source_format is SourceFileFormat.DBUNIT_XML:
        entity = resolve_source_entity(stmt.source_entity, stmt.type, stmt.name)
        source_data = FileUtil.read_dbunit_to_dict_list(
            root.descriptor_dir / source, entity
        )
        if stmt.offset:
            source_data = source_data[stmt.offset :]
    elif source_format is SourceFileFormat.XML:
        source_data = DataSourceRegistry.load_xml_file(
            root.descriptor_dir / source, stmt.cyclic, start_idx, end_idx, offset=stmt.offset
        )
        if source_scripted:
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
