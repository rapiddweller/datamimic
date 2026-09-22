"""Route statement sources through IO-owned readers."""

from typing import Any

from datamimic_ce.engine.dsl.constants.data_type_constants import DATA_TYPE_DICT, DATA_TYPE_LIST
from datamimic_ce.engine.dsl.constants.element_constants import EL_GENERATE, EL_NESTED_KEY, EL_VARIABLE
from datamimic_ce.engine.dsl.enums.distribution_enums import SourceDistribution
from datamimic_ce.engine.dsl.model.constraints import SourceFileFormat, source_file_format, source_file_format_for
from datamimic_ce.engine.dsl.statements.generate_statement import GenerateStatement
from datamimic_ce.engine.dsl.statements.nested_key_statement import NestedKeyStatement
from datamimic_ce.engine.dsl.statements.reference_statement import ReferenceStatement
from datamimic_ce.engine.dsl.statements.statement import Statement
from datamimic_ce.engine.dsl.statements.statement_util import StatementUtil
from datamimic_ce.engine.dsl.statements.variable_statement import VariableStatement
from datamimic_ce.engine.io.api import DataSourcePagination, DataSourceRegistry, FileUtil, MongoDBClient, RdbmsClient
from datamimic_ce.engine.runtime.contexts.context import Context
from datamimic_ce.engine.runtime.contexts.geniter_context import GenIterContext
from datamimic_ce.engine.runtime.contexts.setup_context import SetupContext
from datamimic_ce.engine.runtime.evaluation import evaluate_source_template, interpolate_variables
from datamimic_ce.engine.runtime.logging import logger
from datamimic_ce.engine.runtime.sources.selection import get_distributed_data, get_unique_data


def data_source_cache_key(stmt: Statement) -> tuple[str | None, str | None]:
    """Cache key for a statement's data-source length. Statements may SHARE a name (e.g. three
    <iterate name='db_product'> feeding one table from different sources), so the key must
    include the source - keyed by name alone, the second statement inherits the first one's
    length and silently truncates its rows. A tuple key on real statement types, no string
    concatenation, no duck-typing."""
    if isinstance(stmt, GenerateStatement | VariableStatement | NestedKeyStatement):
        return (stmt.full_name, stmt.source)
    return (stmt.full_name, None)


def window_nested_key_rows(data: list[Any], count: int | None, cyclic: bool | None) -> list[Any]:
    """Select the rows for one nested-key execution."""
    size = len(data) if count is None else count if cyclic else min(count, len(data))
    return DataSourceRegistry.get_cyclic_data_list(
        data=data,
        pagination=DataSourcePagination(0, size),
        cyclic=bool(cyclic),
    )


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
    ds_len: int = 0

    # Check if data source length is already set
    if root_ctx.data_source_len.get(source_id, None) is not None:
        return

    # Check length of script data
    if isinstance(stmt, GenerateStatement) and stmt.script is not None:
        try:
            ds_len = len(ctx.evaluate_python_expression(stmt.script))
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
            except:  # noqa: E722
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
        source_format = source_file_format_for(
            source_element,
            source_str,
            stmt.type,
        )
        # dbunit dataset: one table's row count (checked before the generic .xml branch below).
        if source_format is SourceFileFormat.DBUNIT_XML:
            ds_len = len(
                FileUtil.read_dbunit_to_dict_list(
                    root_ctx.descriptor_dir / source_str, StatementUtil.resolve_source_entity(stmt)
                )
            )
        # 2.1: Check if datasource is csv file
        elif source_format is not None:
            ds_len = len(
                DataSourceRegistry._get_source(
                    str(root_ctx.descriptor_dir / source_str),
                    stmt.separator or ctx.root.default_separator,
                    source_format,
                )
            )
        # 2.4: Check if datasource is memstore
        elif root_ctx.memstore_manager.contain(source_str):
            ds_len = root_ctx.memstore_manager.get_memstore(source_str).get_data_len_by_type(
                StatementUtil.resolve_source_entity(stmt)
            )
        elif root_ctx.get_client_by_id(source_str) is not None:
            client = root_ctx.get_client_by_id(source_str)
            if client is None:
                raise ValueError(f"Client '{source_str}' could not be found in your context, please check your script")
            # handle database collection/table as data source
            selector = stmt.selector if isinstance(stmt, GenerateStatement | VariableStatement) else None
            iteration_selector = stmt.iteration_selector if isinstance(stmt, VariableStatement) else None

            if isinstance(client, RdbmsClient):
                if selector is not None:
                    counted = DataSourceRegistry.rdbms_count_query_length(client, selector, source_str, "selector")
                    if counted is None:
                        return
                    ds_len = counted
                elif iteration_selector is not None:
                    counted = DataSourceRegistry.rdbms_count_query_length(
                        client, iteration_selector, source_str, "iterationSelector"
                    )
                    if counted is None:
                        return
                    ds_len = counted
                elif stmt.source_entity is not None or stmt.type is not None:
                    ds_len = client.count_table_length(table_name=StatementUtil.resolve_source_entity(stmt))

            elif isinstance(client, MongoDBClient):
                if selector is not None:
                    try:
                        ds_len = client.count_query_length(selector)
                    except ValueError:
                        return
                elif (collection := StatementUtil.resolve_source_collection(stmt)) is not None:
                    try:
                        ds_len = client.count(collection_name=collection)
                    except ValueError:
                        return
                elif iteration_selector is not None:
                    try:
                        ds_len = client.count_query_length(query=iteration_selector)
                    except ValueError:
                        logger.error(
                            f"Cannot get length of database source '{source_str}' "
                            f"with iterationSelector '{iteration_selector}'"
                        )
                        return
                else:
                    raise ValueError(
                        "MongoDB source requires at least attribute 'type', 'selector' or 'iterationSelector'"
                    )
            else:
                raise ValueError(f"Cannot determine type of client '{source_id}.{source_str}'")
        else:
            logger.warning(f"Data source '{source_str}' is not supported for length calculation")
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
    source_data: dict | list = []
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
        source_data = FileUtil.read_dbunit_to_dict_list(
            root.descriptor_dir / source, StatementUtil.resolve_source_entity(stmt)
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
            StatementUtil.resolve_source_entity(stmt), pagination, stmt.cyclic
        )
    elif root.clients.get(source) is not None:
        if stmt.offset:
            raise ValueError(
                f"<generate> '{stmt.full_name}': offset= is only supported for file sources, "
                f"not database client '{source}' - use a selector with an SQL/Mongo skip instead"
            )
        client = root.clients[source]
        selector = interpolate_variables(root, stmt.selector or "", prefix, suffix)
        if isinstance(client, MongoDBClient):
            if stmt.selector:
                source_data = client.get_by_page_with_query(query=selector, pagination=pagination)
            elif (collection := StatementUtil.resolve_source_collection(stmt)) is not None:
                source_data = client.get_by_page_with_type(collection_name=collection, pagination=pagination)
            else:
                raise ValueError(
                    "MongoDB source requires at least attribute 'sourceEntity', 'type', 'selector' "
                    "or 'iterationSelector'"
                )
            if not source_data and stmt.contain_mongodb_upsert(root):
                source_data = [{}]
        elif isinstance(client, RdbmsClient):
            if stmt.selector:
                source_data = client.get_by_page_with_query(original_query=selector, pagination=pagination)
            else:
                source_data = client.get_by_page_with_type(
                    table_name=StatementUtil.resolve_source_entity(stmt), pagination=pagination
                )
        else:
            raise ValueError(f"Cannot load data from client: {type(client).__name__}")
    else:
        raise ValueError(f"cannot find data source {source} for iterate task")

    rows = source_data if isinstance(source_data, list) else [source_data]
    return rows, build_from_source


def load_nested_key_source(context: Context, stmt: NestedKeyStatement) -> list[Any] | dict[str, Any]:
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
    if stmt.type == DATA_TYPE_LIST:
        if source_format is SourceFileFormat.CSV:
            separator = stmt.separator or context.root.default_separator
            return FileUtil.read_csv_to_dict_list(context.root.descriptor_dir / source, separator)
        if source_format is SourceFileFormat.JSON:
            return FileUtil.read_json_to_list(context.root.descriptor_dir / source)
        if context.root.memstore_manager.contain(source):
            return context.root.memstore_manager.get_memstore(source).get_data_by_type(
                StatementUtil.resolve_source_entity(stmt), None, stmt.cyclic
            )
        raise ValueError(f"Invalid source '{source}' of nestedkey '{stmt.name}'")

    if stmt.type == DATA_TYPE_DICT:
        if source_format is SourceFileFormat.JSON:
            return FileUtil.read_json_to_dict(context.root.descriptor_dir / source)
        raise ValueError(f"Source of nestedkey having type as 'dict' does not support format {source}")

    if context.root.memstore_manager.contain(source):
        return context.root.memstore_manager.get_memstore(source).get_data_by_type(
            StatementUtil.resolve_source_entity(stmt), None, stmt.cyclic
        )
    raise ValueError(f"Cannot load data from source '{source_expression}' of <nestedKey> '{stmt.name}'")


def finalize_nested_key_source(
    context: Context,
    stmt: NestedKeyStatement,
    data: list[Any] | dict[str, Any],
) -> list[Any] | dict[str, Any]:
    """Apply nested-key source templating and distribution in one boundary owner."""
    source_scripted = (
        stmt.source_script if stmt.source_script is not None else bool(context.root.default_source_scripted)
    )
    result: list[Any] | dict[str, Any] = data
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
) -> list[dict[str, Any]]:
    """Load, map and select reference rows behind one typed datasource boundary."""
    client = context.root.clients.get(stmt.source)
    if not isinstance(client, RdbmsClient | MongoDBClient):
        raise ValueError(
            f"<reference> '{stmt.name}': source '{stmt.source}' is not a "
            "<database> or <mongodb> client (RDBMS and MongoDB are supported)"
        )
    rows = client.get_random_rows_by_columns(stmt.source_type, stmt.source_keys)
    if not rows:
        raise ValueError(f"No data found for reference {stmt.name}")
    records = [dict(zip(stmt.targets, row, strict=True)) for row in rows]

    seed = context.root.stable_distribution_seed(stmt.full_name)
    if stmt.unique:
        return get_unique_data(records, pagination, seed, f"<reference> '{stmt.name}'")

    distribution = SourceDistribution.coerce(stmt.distribution)
    if (stmt.distribution is not None and distribution is not SourceDistribution.RANDOM) or stmt.cyclic:
        if distribution is SourceDistribution.ORDERED or (stmt.distribution is None and stmt.cyclic):
            return _ordered_reference_rows(records, stmt, pagination)
        return get_distributed_data(records, pagination, stmt.cyclic, seed, distribution)

    size = pagination.limit if pagination is not None else 1
    return [context.rng.choice(records) for _ in range(size)]


def _ordered_reference_rows(
    records: list[dict[str, Any]],
    stmt: ReferenceStatement,
    pagination: DataSourcePagination | None,
) -> list[dict[str, Any]]:
    if pagination is None:
        return records
    start = pagination.skip
    size = pagination.limit
    if stmt.cyclic:
        return [records[(start + index) % len(records)] for index in range(size)]
    if start + size > len(records):
        raise ValueError(
            f"<reference> '{stmt.name}' distribution='ordered' needs {start + size} rows "
            f'but the source has only {len(records)} (use cyclic="true" to wrap around)'
        )
    return records[start : start + size]
