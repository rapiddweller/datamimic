"""Route statement sources through IO-owned readers."""

from collections.abc import Sized

from datamimic_ce.engine.dsl.api import (
    DATA_TYPE_DICT,
    EL_GENERATE,
    EL_NESTED_KEY,
    EL_VARIABLE,
    ExportOperation,
    GenerateStatement,
    NestedKeyStatement,
    ReferenceStatement,
    SourceDistribution,
    Statement,
    VariableStatement,
)
from datamimic_ce.engine.dsl.vocabulary.source_capabilities import (
    SourceFileFormat,
    source_file_format,
    source_file_format_for,
)
from datamimic_ce.engine.io.api import (
    CountSourceRequest,
    DataSourcePagination,
    DataSourceRegistry,
    FileUtil,
    count_source,
    database_get_by_page_with_query,
    database_get_by_page_with_type,
    get_distributed_data,
    is_mongodb_client,
    is_rdbms_client,
    read_nested_key_source,
    read_reference_rows,
    resolve_source_collection,
    resolve_source_entity,
    select_reference_rows,
)
from datamimic_ce.engine.runtime.contexts.context import Context, SetupContext
from datamimic_ce.engine.runtime.contexts.geniter_context import GenIterContext
from datamimic_ce.engine.runtime.logging import logger
from datamimic_ce.engine.runtime.scripting.evaluation import evaluate_source_template, interpolate_variables


def data_source_cache_key(stmt: Statement) -> tuple[str | None, str | None]:
    """Cache key for a statement's data-source length. Statements may SHARE a name (e.g. three
    <iterate name='db_product'> feeding one table from different sources), so the key must
    include the source - keyed by name alone, the second statement inherits the first one's
    length and silently truncates its rows. A tuple key on real statement types, no string
    concatenation, no duck-typing."""
    if isinstance(stmt, GenerateStatement | VariableStatement | NestedKeyStatement):
        return (stmt.full_name, stmt.source)
    return (stmt.full_name, None)


def has_mongodb_upsert_target(targets: set[str], setup_context: SetupContext) -> bool:
    for target in targets:
        if "." in target:
            consumer, operation = target.split(".", 1)
            if operation == ExportOperation.UPSERT.value and is_mongodb_client(
                setup_context.get_client_by_id(consumer)
            ):
                return True
    return False


def set_data_source_length(ctx: SetupContext | GenIterContext, stmt: Statement) -> None:
    """
    Calculate length of data source then save into context
    :param ctx:
    :param stmt:
    :return:
    """
    # TODO: consider to paginate source of element "reference"
    if isinstance(stmt, ReferenceStatement):
        return
    if not isinstance(stmt, GenerateStatement | VariableStatement | NestedKeyStatement):
        return

    root_ctx = ctx.root
    source_id: tuple[str | None, str | None] = data_source_cache_key(stmt)
    # Check if data source length is already set
    if root_ctx.data_source_len.get(source_id, None) is not None:
        return

    ds_len: int | None

    # Check length of script data
    if isinstance(stmt, GenerateStatement) and stmt.script is not None:
        try:
            data = ctx.evaluate_python_expression(stmt.script)
            if not isinstance(data, Sized):
                raise TypeError("Script source result has no length")
            ds_len = len(data)
        except Exception as e:
            logger.debug(f"Cannot get length of script data before generating data: {e}")
            return
    # Check length of data source
    else:
        source_str = stmt.source
        if source_str is None:
            return
        # Try to evaluate script as source string
        # Ignore to check scripted source if eval failed in pre-execute task
        if source_str.startswith("{") and source_str.endswith("}"):
            try:
                source_str = ctx.evaluate_python_expression(source_str[1:-1])
            except Exception:
                return
            if not isinstance(source_str, str):
                return

        # 2: Get source info from ctx client (e.g. checking if it is SQL, MongoDB or CSV source)

        # Check if source is data source file or database collection/table.
        if isinstance(stmt, GenerateStatement):
            source_element = EL_GENERATE
        elif isinstance(stmt, VariableStatement):
            source_element = EL_VARIABLE
        elif isinstance(stmt, NestedKeyStatement):
            source_element = EL_NESTED_KEY
        else:
            return
        source_format = source_file_format_for(source_element, source_str, stmt.type)
        memstore = (
            root_ctx.memstore_manager.get_memstore(source_str)
            if source_format is None
            and root_ctx.memstore_manager.contain(source_str)
            else None
        )
        client = None
        if source_format is None and memstore is None and root_ctx.get_client_by_id(source_str) is not None:
            client = root_ctx.get_client_by_id(source_str)
            if client is None:
                raise ValueError(f"Client '{source_str}' could not be found in your context, please check your script")
        selector = (
            stmt.selector
            if client is not None and isinstance(stmt, GenerateStatement | VariableStatement)
            else None
        )
        iteration_selector = (
            stmt.iteration_selector if client is not None and isinstance(stmt, VariableStatement) else None
        )
        ds_len = count_source(
            CountSourceRequest(
                source=source_str,
                source_id=source_id,
                descriptor_dir=root_ctx.descriptor_dir,
                element=source_element,
                source_type=stmt.type,
                source_entity=stmt.source_entity,
                name=stmt.name,
                separator=(
                    stmt.separator
                    if source_format is not None and source_format is not SourceFileFormat.DBUNIT_XML
                    else None
                ),
                default_separator=(
                    root_ctx.default_separator
                    if source_format is not None and source_format is not SourceFileFormat.DBUNIT_XML
                    else ""
                ),
                selector=selector,
                iteration_selector=iteration_selector,
            ),
            memstore,
            client,
        )
        if ds_len is None:
            return

    # 3: Set length of data source. offset= shrinks the available window - the count
    # default and the count-above-source warning must both see the post-offset size.
    if isinstance(stmt, GenerateStatement) and stmt.offset:
        ds_len = max(0, ds_len - stmt.offset)
    root_ctx.data_source_len[source_id] = ds_len


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
            if not source_data and has_mongodb_upsert_target(stmt.targets, root):
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


def load_nested_key_source(context: Context, stmt: NestedKeyStatement) -> object:
    """Resolve and load the raw source owned by one nested key."""
    source_expression = stmt.source
    if source_expression is None:
        raise ValueError(f"<nestedKey> '{stmt.name}' has no source to load")
    source = (
        context.evaluate_python_expression(source_expression[1:-1])
        if source_expression.startswith("{") and source_expression.endswith("}")
        else source_expression
    )
    if not isinstance(source, str):
        raise ValueError(f"Source expression of <nestedKey> '{stmt.name}' must evaluate to a string")
    source_format = source_file_format_for(EL_NESTED_KEY, source, stmt.type)
    memstore = None
    if source_format is None and stmt.type != DATA_TYPE_DICT and context.root.memstore_manager.contain(source):
        memstore = context.root.memstore_manager.get_memstore(source)
    return read_nested_key_source(
        context.root.descriptor_dir,
        source_expression,
        source,
        stmt.type,
        stmt.source_entity,
        stmt.name,
        stmt.separator if source_format is SourceFileFormat.CSV else None,
        context.root.default_separator if source_format is SourceFileFormat.CSV else "",
        stmt.cyclic,
        memstore,
    )


def finalize_nested_key_source(
    context: Context,
    stmt: NestedKeyStatement,
    data: object,
) -> object:
    """Apply nested-key source templating and distribution in one boundary owner."""
    source_scripted = (
        stmt.source_script if stmt.source_script is not None else bool(context.root.default_source_scripted)
    )
    result = data
    if source_scripted:
        prefix = stmt.variable_prefix or context.root.default_variable_prefix
        suffix = stmt.variable_suffix or context.root.default_variable_suffix
        evaluated = evaluate_source_template(context, result, prefix, suffix)
        if not isinstance(evaluated, list | dict):
            raise ValueError(f"Source template of <nestedKey> '{stmt.name}' must evaluate to list or dict")
        result = evaluated
    if isinstance(result, list) and stmt.distribution.loads_all:
        seed = context.root.get_distribution_seed()
        result = get_distributed_data(result, None, stmt.cyclic, seed, stmt.distribution)
    return result


def reference_uses_shared_cycle(stmt: ReferenceStatement) -> bool:
    """Whether an unpaged reference needs root-owned rotation across rebuilt tasks."""
    if stmt.cyclic:
        return True
    return stmt.distribution is not None and SourceDistribution.coerce(stmt.distribution) is not (
        SourceDistribution.RANDOM
    )


def load_reference_source(
    context: Context,
    stmt: ReferenceStatement,
    pagination: DataSourcePagination | None,
) -> list[dict[str, object]]:
    """Load, map and select reference rows behind one typed datasource boundary."""
    client = context.root.clients.get(stmt.source)
    records = read_reference_rows(client, stmt.source, stmt.source_type, stmt.source_keys, stmt.targets, stmt.name)

    seed = context.root.stable_distribution_seed(stmt.full_name)
    distribution = SourceDistribution.coerce(stmt.distribution)
    random_rng = None
    if not stmt.unique and distribution is SourceDistribution.RANDOM and not stmt.cyclic:
        size = pagination.limit if pagination is not None else 1
        if size > 0:
            random_rng = context.rng
    default_cyclic_ordered = stmt.distribution is None and stmt.cyclic
    return select_reference_rows(
        records,
        pagination,
        stmt.cyclic,
        distribution,
        stmt.distribution is not None,
        stmt.unique,
        seed,
        f"<reference> '{stmt.name}'",
        random_rng,
        default_cyclic_ordered,
    )
