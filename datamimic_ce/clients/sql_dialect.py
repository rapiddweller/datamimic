# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""The one place CE reads or writes dialect-specific SQL text.

Reading SQL (a selector's own ORDER BY terms / row limit, statement boundaries in a script) goes through
sqlglot in the connection's dialect, never through regex or string splitting. Swapping how SQL is
parsed or rendered means changing this module only; RdbmsClient keeps the database I/O.
"""

from collections.abc import Iterable
from dataclasses import dataclass

import sqlglot
from sqlglot import exp
from sqlglot.dialects import Dialects
from sqlglot.tokens import Token, TokenType

from datamimic_ce.enums.dbms_enums import Dbms
from datamimic_ce.logger import logger


@dataclass(frozen=True)
class DialectRules:
    """What CE must know about one database system to write and split its SQL text. Rendering stays
    string-based (not sqlglot's generator) so the user's selector runs exactly as written."""

    sqlglot_dialect: Dialects
    executes_one_statement_per_call: bool
    pages_with_offset_fetch: bool
    accepts_as_before_subquery_alias: bool
    accepts_order_by_in_derived_table: bool
    has_plsql_blocks: bool


DIALECT_RULES: dict[Dbms, DialectRules] = {
    Dbms.SQLITE: DialectRules(
        sqlglot_dialect=Dialects.SQLITE,
        executes_one_statement_per_call=True,
        pages_with_offset_fetch=False,
        accepts_as_before_subquery_alias=True,
        accepts_order_by_in_derived_table=True,
        has_plsql_blocks=False,
    ),
    Dbms.POSTGRESQL: DialectRules(
        sqlglot_dialect=Dialects.POSTGRES,
        executes_one_statement_per_call=False,
        pages_with_offset_fetch=False,
        accepts_as_before_subquery_alias=True,
        accepts_order_by_in_derived_table=True,
        has_plsql_blocks=False,
    ),
    Dbms.MYSQL: DialectRules(
        sqlglot_dialect=Dialects.MYSQL,
        executes_one_statement_per_call=True,
        pages_with_offset_fetch=False,
        accepts_as_before_subquery_alias=True,
        accepts_order_by_in_derived_table=True,
        has_plsql_blocks=False,
    ),
    Dbms.MSSQL: DialectRules(
        sqlglot_dialect=Dialects.TSQL,
        executes_one_statement_per_call=False,
        pages_with_offset_fetch=True,
        accepts_as_before_subquery_alias=True,
        accepts_order_by_in_derived_table=False,
        has_plsql_blocks=False,
    ),
    Dbms.ORACLE: DialectRules(
        sqlglot_dialect=Dialects.ORACLE,
        executes_one_statement_per_call=True,
        pages_with_offset_fetch=True,
        accepts_as_before_subquery_alias=False,
        accepts_order_by_in_derived_table=True,
        has_plsql_blocks=True,
    ),
}

ROW_LIMIT_TOKENS = frozenset({TokenType.LIMIT, TokenType.OFFSET, TokenType.FETCH})

# The oracle tokenizer yields DECLARE, IF and LOOP as plain identifiers, so they compare by token text.
PLSQL_DECLARE_KEYWORD = "DECLARE"
PLSQL_END_SUFFIXES_WITHOUT_BLOCK = frozenset({"IF", "LOOP"})


def count_query(query: str, dbms: Dbms) -> str:
    return f"SELECT COUNT(*) FROM {_derived_table(query, dbms)}"


def column_probe_query(query: str, dbms: Dbms) -> str:
    """Returns no rows; its result keys are the selector's output columns."""
    return f"SELECT * FROM {_derived_table(query, dbms)} WHERE 1 = 0"


@dataclass(frozen=True)
class SelectorPage:
    """How to read one page of a selector: run ``sql``, then keep ``rows`` of its result."""

    sql: str
    rows: slice


def selector_page(query: str, dbms: Dbms, skip: int, limit: int, columns: list[str]) -> SelectorPage:
    """One page of a selector in a deterministic order (#228).

    The selector's own top-level ORDER BY stays first and verbatim, so it remains the source order;
    every output column it does not already sort by follows as a positional tie-breaker (SQL Server
    rejects a column listed twice). Without an own ORDER BY, all output columns order it. The terms go
    before the selector's own row limit (LIMIT/TOP/FETCH/OFFSET), which makes that bounded subset
    deterministic too; a bounded selector is then read whole for every page and sliced here, because
    re-sorting it outside would lose its order (cost: pages x the selector's own limit). Any other
    selector is paged by the database. An unparseable selector
    is wrapped and ordered by all output columns.
    """
    parsed = _parse_selector(query, dbms)
    if parsed is None:
        wrapped = f"SELECT * FROM {_derived_table(query, dbms)} {_order_by(range(1, len(columns) + 1))}"
        return SelectorPage(f"{wrapped} {_paging_clause(dbms, skip, limit)}", slice(None))
    ordered = _with_deterministic_order(query, dbms, parsed, columns)
    if _has_own_row_limit(parsed):
        return SelectorPage(ordered, slice(skip, skip + limit))
    return SelectorPage(f"{ordered} {_paging_clause(dbms, skip, limit)}", slice(None))


def split_script(script: str, dbms: Dbms) -> list[str]:
    """Statements of an <execute> SQL script, cut at the tokenizer's statement-ending semicolons (never
    one inside a literal or comment). Oracle PL/SQL blocks (DECLARE/BEGIN ... END;) stay whole with their
    closing semicolon; other statements drop it. Batch-capable systems get the script unchanged."""
    rules = DIALECT_RULES[dbms]
    if not rules.executes_one_statement_per_call:
        return [script]
    tokens = sqlglot.tokenize(script, read=rules.sqlglot_dialect)
    statements: list[str] = []
    start = 0
    while start < len(tokens):
        block_end = _plsql_block_end(tokens, start) if rules.has_plsql_blocks else None
        if block_end is not None:
            statements.append(script[tokens[start].start : tokens[block_end].end + 1])
            start = block_end + 1
            continue
        end = _next_semicolon(tokens, start)
        if end > start:
            statements.append(script[tokens[start].start : tokens[end - 1].end + 1])
        start = end + 1
    return statements


def _parse_selector(query: str, dbms: Dbms) -> exp.Query | None:
    """The selector as a query AST; None when it is not a parseable query."""
    try:
        parsed = sqlglot.parse_one(_statement_text(query, dbms), read=DIALECT_RULES[dbms].sqlglot_dialect)
    except sqlglot.errors.ParseError as error:
        logger.warning(f"Cannot parse selector, paging it in canonical column order: {error}")
        return None
    return parsed if isinstance(parsed, exp.Query) else None


def _top_level_order(parsed: exp.Query) -> exp.Order | None:
    """The ORDER BY of the whole statement. The T-SQL parser attaches a union's ORDER BY to its last branch."""
    order = parsed.args.get("order")
    if order is None and isinstance(parsed, exp.SetOperation):
        order = parsed.expression.args.get("order")
    return order


def _has_own_row_limit(parsed: exp.Query) -> bool:
    candidates = [parsed, parsed.expression] if isinstance(parsed, exp.SetOperation) else [parsed]
    return any(node.args.get("limit") is not None or node.args.get("offset") is not None for node in candidates)


def _tie_breaker_positions(order: exp.Order, parsed: exp.Query, columns: list[str]) -> list[int]:
    """Output positions (1-based) the ORDER BY does not already sort by. A term references a position as a
    positional literal, or as a column that position projects. With an explicit projection list that match
    is on the projected expression, qualifier included (``ORDER BY a.id`` covers ``a.id AS a_id``, not
    ``b.id AS b_id``); behind ``*`` only the output name is known, so only an unambiguous name counts."""
    projections = parsed.selects
    explicit = len(projections) == len(columns) and not any(_is_star(projection) for projection in projections)
    referenced: set[int] = set()
    for term in order.expressions:
        referenced |= _referenced_positions(term.this, projections if explicit else None, columns)
    return [position for position in range(1, len(columns) + 1) if position not in referenced]


def _is_star(projection: exp.Expr) -> bool:
    return isinstance(projection, exp.Star) or (isinstance(projection, exp.Column) and projection.is_star)


def _referenced_positions(key: exp.Expr, projections: list[exp.Expr] | None, columns: list[str]) -> set[int]:
    if isinstance(key, exp.Literal) and key.is_int:
        return {int(key.name)}
    if not isinstance(key, exp.Column):
        return set()
    if projections is None:
        by_name = {index + 1 for index, column in enumerate(columns) if column.casefold() == key.name.casefold()}
        return by_name if len(by_name) == 1 else set()
    return {index + 1 for index, projection in enumerate(projections) if _projects_column(projection, key)}


def _projects_column(projection: exp.Expr, key: exp.Column) -> bool:
    """The projection outputs the ordered column: an unqualified term by the output name, or the same source
    column, where a missing qualifier on either side matches any table."""
    if not key.table and projection.alias_or_name.casefold() == key.name.casefold():
        return True
    source = projection.this if isinstance(projection, exp.Alias) else projection
    if not isinstance(source, exp.Column) or source.name.casefold() != key.name.casefold():
        return False
    return not key.table or not source.table or source.table.casefold() == key.table.casefold()


def _order_by(positions: Iterable[int]) -> str:
    return "ORDER BY " + ", ".join(map(str, positions))


def _with_deterministic_order(query: str, dbms: Dbms, parsed: exp.Query, columns: list[str]) -> str:
    """The selector with order terms inserted where its top-level ORDER BY clause ends, i.e. before its
    own row limit or at its last token. Everything else of the user's text stays as written."""
    order = _top_level_order(parsed)
    if order is None:
        terms = f" {_order_by(range(1, len(columns) + 1))}"
    else:
        tie_breakers = _tie_breaker_positions(order, parsed, columns)
        if not tie_breakers:
            return _statement_text(query, dbms)
        terms = ", " + ", ".join(map(str, tie_breakers))
    insert_at, end = _order_terms_position(query, dbms)
    return f"{query[:insert_at].rstrip()}{terms} {query[insert_at:end]}".rstrip()


def _order_terms_position(query: str, dbms: Dbms) -> tuple[int, int]:
    """(text index where extra ORDER BY terms go, text index just past the statement's last token).
    Extra terms go before the first top-level LIMIT/OFFSET/FETCH after the top-level ORDER BY, else at
    the end; trailing semicolons and comments are dropped because appended clauses would land in them."""
    tokens = sqlglot.tokenize(query, read=DIALECT_RULES[dbms].sqlglot_dialect)
    statement_end = max((token.end + 1 for token in tokens if token.token_type is not TokenType.SEMICOLON), default=0)
    depth = 0
    after_order_by = 0
    row_limit_start: int | None = None
    for token in tokens:
        if token.token_type is TokenType.L_PAREN:
            depth += 1
        elif token.token_type is TokenType.R_PAREN:
            depth -= 1
        elif depth == 0 and token.token_type is TokenType.ORDER_BY:
            after_order_by, row_limit_start = token.start, None
        elif (
            depth == 0
            and token.token_type in ROW_LIMIT_TOKENS
            and row_limit_start is None
            and token.start > after_order_by
        ):
            row_limit_start = token.start
    return (row_limit_start if row_limit_start is not None else statement_end), statement_end


def _statement_text(query: str, dbms: Dbms) -> str:
    return query[: _order_terms_position(query, dbms)[1]]


def _paging_clause(dbms: Dbms, skip: int, limit: int) -> str:
    if DIALECT_RULES[dbms].pages_with_offset_fetch:
        return f"OFFSET {skip} ROWS FETCH NEXT {limit} ROWS ONLY"
    return f"LIMIT {limit} OFFSET {skip}"


def _derived_table(query: str, dbms: Dbms) -> str:
    """``(<statement>) [AS] original_query``, valid as a derived table in the dialect: without the selector's
    trailing semicolon or comment, which would end or swallow the enclosing query. SQL Server accepts an
    ORDER BY there only together with OFFSET/TOP, so an ordered selector without a row limit gets
    OFFSET 0 ROWS."""
    rules = DIALECT_RULES[dbms]
    statement = _statement_text(query, dbms)
    if not rules.accepts_order_by_in_derived_table:
        parsed = _parse_selector(query, dbms)
        if parsed is not None and _top_level_order(parsed) is not None and not _has_own_row_limit(parsed):
            statement = f"{statement} OFFSET 0 ROWS"
    alias = "AS original_query" if rules.accepts_as_before_subquery_alias else "original_query"
    return f"({statement}) {alias}"


def _next_semicolon(tokens: list[Token], start: int) -> int:
    index = start
    while index < len(tokens) and tokens[index].token_type is not TokenType.SEMICOLON:
        index += 1
    return index


def _opens_plsql_block(tokens: list[Token], start: int) -> bool:
    """DECLARE or BEGIN before the statement's first semicolon: an anonymous block, or e.g.
    CREATE TRIGGER ... BEGIN ... END;"""
    return any(
        token.token_type is TokenType.BEGIN or token.text.upper() == PLSQL_DECLARE_KEYWORD
        for token in tokens[start : _next_semicolon(tokens, start)]
    )


def _plsql_block_end(tokens: list[Token], start: int) -> int | None:
    """Index of the semicolon closing the PL/SQL block that starts at ``start``, or None for a plain
    statement. BEGIN and CASE open a nesting level, END closes one; END IF / END LOOP close none, and
    END CASE is one END."""
    if not _opens_plsql_block(tokens, start):
        return None
    open_levels = 0
    closed = False
    index = start
    while index < len(tokens):
        token = tokens[index]
        following = tokens[index + 1] if index + 1 < len(tokens) else None
        if closed and token.token_type is TokenType.SEMICOLON:
            return index
        if token.token_type in (TokenType.BEGIN, TokenType.CASE):
            open_levels += 1
        elif token.token_type is TokenType.END:
            names_its_block = following is not None and (
                following.text.upper() in PLSQL_END_SUFFIXES_WITHOUT_BLOCK or following.token_type is TokenType.CASE
            )
            if following is None or following.text.upper() not in PLSQL_END_SUFFIXES_WITHOUT_BLOCK:
                open_levels -= 1
                closed = open_levels == 0
            if names_its_block:
                index += 1
        index += 1
    return len(tokens) - 1
