"""Runtime source operations for length statements."""

from collections.abc import Sized

from datamimic_ce.engine.dsl.api import (
    ATTR_COLUMNS,
    ATTR_COUNT,
    ATTR_CYCLIC,
    ATTR_DISTRIBUTION,
    ATTR_OFFSET,
    ATTR_SOURCE,
    ATTR_SOURCE_SCRIPTED,
    ATTR_UNIQUE,
    ATTR_WEIGHT_COLUMN,
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
from datamimic_ce.engine.dsl.vocabulary.enums.distribution_enums import SourceDistribution
from datamimic_ce.engine.dsl.vocabulary.source_capabilities import (
    SourceFileFormat,
    source_file_format,
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
    stmt: GenerateStatement, source: str, *, memstore: bool, client: bool, root: SetupContext
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
    if root.source_scripted(stmt.source_script):
        raise invalid_source_error(
            code=IssueCode.GENERATE_ROW_SELECTION_SOURCE_SCRIPTED,
            stmt_name=stmt.full_name,
            location=DescriptorLocation(EL_GENERATE, attribute=ATTR_SOURCE_SCRIPTED),
        )


def _refuse_weighted_entity(stmt: GenerateStatement, source: str, requirement: str, attribute: str) -> None:
    raise invalid_source_error(
        code=IssueCode.SOURCE_GENERATE_WEIGHTED_ENTITY_CONTRACT,
        stmt_name=stmt.full_name,
        source_str=source,
        requirement=requirement,
        location=DescriptorLocation(EL_GENERATE, attribute=attribute),
    )


def refuse_weighted_entity_contract(stmt: GenerateStatement, source: str) -> None:
    """A .wgt.ent.csv source draws count rows by weightColumn with replacement. The statement must name both and
    set nothing that the draw ignores; weightColumn on any other source is ignored too. Same contract as EE."""
    if source_file_format(source) is not SourceFileFormat.WEIGHTED_ENTITY_CSV:
        if stmt.weight_column is not None:
            _refuse_weighted_entity(
                stmt, source, "sets weightColumn, which applies to a .wgt.ent.csv source only", ATTR_WEIGHT_COLUMN
            )
        return
    if stmt.weight_column is None:
        _refuse_weighted_entity(stmt, source, "requires the weightColumn attribute", ATTR_WEIGHT_COLUMN)
    if stmt.count is None:
        _refuse_weighted_entity(stmt, source, "requires an explicit count: the draw has no end of its own", ATTR_COUNT)
    if stmt.distribution is not SourceDistribution.RANDOM:
        _refuse_weighted_entity(
            stmt, source, "draws by weight: remove distribution, it cannot select another order", ATTR_DISTRIBUTION
        )
    ignored = (
        (ATTR_UNIQUE, bool(stmt.unique)),
        (ATTR_CYCLIC, bool(stmt.cyclic)),
        (ATTR_OFFSET, bool(stmt.offset)),
        (ATTR_WHERE, stmt.where is not None),
        (ATTR_COLUMNS, stmt.columns is not None),
        # Only an explicit sourceScripted is refused: the setup-wide default must not break a weighted source.
        (ATTR_SOURCE_SCRIPTED, bool(stmt.source_script)),
    )
    for attribute, is_set in ignored:
        if is_set:
            _refuse_weighted_entity(stmt, source, f"draws by weight: the draw ignores {attribute}", attribute)


def forget_written_source_lengths(root_ctx: SetupContext, written: set[str]) -> None:
    """Drop the cached length of every source that a page export just wrote to (a table or a memstore): an inner
    statement of the next page counts it again instead of keeping the length of the first row (#641)."""
    for key in [key for key in root_ctx.data_source_len if key[1] in written]:
        del root_ctx.data_source_len[key]


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
    # An outermost statement reads its length when it runs: an entry left by an earlier statement with the same key
    # (name, source, where) can predate a memstore write or name another entity (#641). An inner statement runs
    # once per parent row and keeps the length counted for the first row.
    if isinstance(ctx, SetupContext) and not ctx.within_generate:
        if source_id in root_ctx.data_source_len:
            del root_ctx.data_source_len[source_id]
    elif root_ctx.data_source_len.get(source_id, None) is not None:
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
            if source_format is None and root_ctx.memstore_manager.contain(source_str)
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
            refuse_weighted_entity_contract(stmt, source_str)
            refuse_row_selection(
                stmt,
                source_str,
                memstore=memstore is not None,
                client=client is not None,
                root=root_ctx,
            )
        selector = (
            stmt.selector if client is not None and isinstance(stmt, GenerateStatement | VariableStatement) else None
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
