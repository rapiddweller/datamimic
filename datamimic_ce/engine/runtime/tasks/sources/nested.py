"""Runtime source operations for nested statements."""

from datamimic_ce.engine.dsl.api import (
    DATA_TYPE_DICT,
    EL_NESTED_KEY,
    NestedKeyStatement,
)
from datamimic_ce.engine.dsl.vocabulary.source_capabilities import (
    SourceFileFormat,
    source_file_format_for,
)
from datamimic_ce.engine.io.api import (
    get_distributed_data,
    read_nested_key_source,
)
from datamimic_ce.engine.runtime.contexts.context import Context
from datamimic_ce.engine.runtime.scripting.evaluation import evaluate_source_template


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
