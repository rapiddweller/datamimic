"""Runtime source operations for length statements."""

from collections.abc import Sized

from datamimic_ce.engine.dsl.api import (
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
)
from datamimic_ce.engine.runtime.contexts.context import SetupContext
from datamimic_ce.engine.runtime.contexts.geniter_context import GenIterContext
from datamimic_ce.engine.runtime.logging import logger


def data_source_cache_key(stmt: Statement) -> tuple[str | None, str | None]:
    """Cache key for a statement's data-source length. Statements may SHARE a name (e.g. three
    <iterate name='db_product'> feeding one table from different sources), so the key must
    include the source - keyed by name alone, the second statement inherits the first one's
    length and silently truncates its rows. A tuple key on real statement types, no string
    concatenation, no duck-typing."""
    if isinstance(stmt, GenerateStatement | VariableStatement | NestedKeyStatement):
        return (stmt.full_name, stmt.source)
    return (stmt.full_name, None)


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
