"""Runtime source operations for length statements."""

from collections.abc import Sized

from datamimic_ce.engine.dsl.api import (
    ATTR_COLUMNS,
    ATTR_SOURCE,
    ATTR_SOURCE_SCRIPTED,
    ATTR_WHERE,
    EL_GENERATE,
    EL_NESTED_KEY,
    EL_VARIABLE,
    GenerateStatement,
    NestedKeyStatement,
    ReferenceStatement,
    Statement,
    VariableStatement,
)
from datamimic_ce.engine.dsl.vocabulary.source_capabilities import (
    SourceFileFormat,
    source_file_format_for,
)
from datamimic_ce.engine.io.api import (
    CountSourceRequest,
    count_source,
    is_database_client,
)
from datamimic_ce.engine.runtime.contexts.context import SetupContext
from datamimic_ce.engine.runtime.contexts.geniter_context import GenIterContext
from datamimic_ce.engine.runtime.logging import logger
from datamimic_ce.engine.runtime.scripting.evaluation import WhereCondition
from datamimic_ce.errors import DescriptorLocation, IssueCode, invalid_source_error


def data_source_cache_key(stmt: Statement) -> tuple[str | None, str | None, str | None]:
    """Cache key for a statement's data-source length. Statements may SHARE a name (e.g. three
    <iterate name='db_product'> feeding one table from different sources), so the key must
    include the source and the where= condition - keyed without them, the second statement inherits
    the first one's length and silently truncates its rows. A tuple key on real statement types, no
    string concatenation, no duck-typing."""
    if isinstance(stmt, GenerateStatement):
        return (stmt.full_name, stmt.source, stmt.where)
    if isinstance(stmt, VariableStatement | NestedKeyStatement):
        return (stmt.full_name, stmt.source, None)
    return (stmt.full_name, None, None)


def refuse_row_selection(
    stmt: GenerateStatement, source: str, *, memstore: bool, client: bool, default_scripted: bool
) -> None:
    """where= and columns= select file rows only. The length pass reads every source first, so the refusal comes
    before any count, row condition or page."""
    attribute = ATTR_WHERE if stmt.where is not None else ATTR_COLUMNS if stmt.columns is not None else None
    if attribute is None:
        return
    if memstore or client:
        raise invalid_source_error(
            code=IssueCode.GENERATE_ROW_SELECTION_FILE_ONLY,
            stmt_name=stmt.full_name,
            attribute=attribute,
            source_kind="memstore" if memstore else "database client",
            source_str=source,
            location=DescriptorLocation(EL_GENERATE, attribute=ATTR_SOURCE),
        )
    if stmt.source_script if stmt.source_script is not None else default_scripted:
        raise invalid_source_error(
            code=IssueCode.GENERATE_ROW_SELECTION_SOURCE_SCRIPTED,
            stmt_name=stmt.full_name,
            location=DescriptorLocation(EL_GENERATE, attribute=ATTR_SOURCE_SCRIPTED),
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
    source_id = data_source_cache_key(stmt)
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
            logger.debug(f"Cannot get length of script data before generating data: {type(e).__name__}")
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
                evaluated_source = ctx.evaluate_python_expression(source_str[1:-1])
            except Exception:
                return
            if not isinstance(evaluated_source, str):
                return
            source_str = evaluated_source

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
            # A blank selector holds no query: refuse it before the first count or read (#397).
            blank = stmt.blank_selector_attribute if isinstance(stmt, GenerateStatement | VariableStatement) else None
            if blank is not None and is_database_client(client):
                raise invalid_source_error(
                    code=IssueCode.SOURCE_SELECTOR_BLANK,
                    attribute=blank,
                    location=DescriptorLocation(source_element, attribute=blank),
                )
        if isinstance(stmt, GenerateStatement):
            refuse_row_selection(
                stmt,
                source_str,
                memstore=memstore is not None,
                client=client is not None,
                default_scripted=bool(root_ctx.default_source_scripted),
            )
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
                source_id=(stmt.full_name, stmt.source),
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
                where=(
                    WhereCondition(stmt.where, stmt.full_name)
                    if isinstance(stmt, GenerateStatement) and stmt.where is not None
                    else None
                ),
                columns=stmt.columns if isinstance(stmt, GenerateStatement) else None,
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
