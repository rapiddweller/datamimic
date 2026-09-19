# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""The one place CE reads or writes dialect-specific SQL text.

Reading SQL (a selector's own ORDER BY / row limit, statement boundaries in a script) goes through
sqlglot in the connection's dialect, never through regex or string splitting. Swapping how SQL is
parsed or rendered means changing this module only; RdbmsClient keeps the database I/O.
"""

from dataclasses import dataclass

import sqlglot
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

# The oracle tokenizer yields DECLARE, IF and LOOP as plain identifiers, so they compare by token text.
PLSQL_DECLARE_KEYWORD = "DECLARE"
PLSQL_END_SUFFIXES_WITHOUT_BLOCK = frozenset({"IF", "LOOP"})


@dataclass(frozen=True)
class SelectorShape:
    owns_order: bool
    owns_row_limit: bool

    @property
    def keeps_own_order(self) -> bool:
        """Its own top-level ORDER BY is the source order; with a row limit it is a subset paged canonically."""
        return self.owns_order and not self.owns_row_limit


def selector_shape(query: str, dbms: Dbms) -> SelectorShape:
    """Top-level ORDER BY and row limit (LIMIT/TOP/FETCH/OFFSET) of a selector. One inside a subquery,
    window function, literal or comment does not count. An unparseable selector reports neither."""
    try:
        parsed = sqlglot.parse_one(query, read=DIALECT_RULES[dbms].sqlglot_dialect)
    except sqlglot.errors.ParseError as error:
        logger.warning(f"Cannot parse selector, paging it in canonical column order: {error}")
        return SelectorShape(owns_order=False, owns_row_limit=False)
    return SelectorShape(
        owns_order=parsed.args.get("order") is not None,
        owns_row_limit=parsed.args.get("limit") is not None or parsed.args.get("offset") is not None,
    )


def count_query(query: str, dbms: Dbms) -> str:
    return f"SELECT COUNT(*) FROM {_derived_table(query, dbms)}"


def column_probe_query(query: str, dbms: Dbms) -> str:
    """Returns no rows; its result keys are the selector's output columns."""
    return f"SELECT * FROM {_derived_table(query, dbms)} WHERE 1 = 0"


def paged_selector_query(query: str, dbms: Dbms, skip: int, limit: int, column_count: int | None) -> str:
    """One OFFSET page of a selector.

    ``column_count=None`` pages the selector in place, in its own order (``SelectorShape.keeps_own_order``):
    wrapped in a derived table, the database may drop that order. Otherwise the page is ordered by every
    output column, a canonical order, because an arbitrary query has no known key.
    """
    paging = _paging_clause(dbms, skip, limit)
    if column_count is None:
        return f"{_without_terminator(query)} {paging}"
    order_by = "ORDER BY " + ", ".join(str(position) for position in range(1, column_count + 1))
    return f"SELECT * FROM {_derived_table(query, dbms)} {order_by} {paging}"


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


def _without_terminator(query: str) -> str:
    return query.rstrip().rstrip(";")


def _paging_clause(dbms: Dbms, skip: int, limit: int) -> str:
    if DIALECT_RULES[dbms].pages_with_offset_fetch:
        return f"OFFSET {skip} ROWS FETCH NEXT {limit} ROWS ONLY"
    return f"LIMIT {limit} OFFSET {skip}"


def _derived_table(query: str, dbms: Dbms) -> str:
    """``(<query>) [AS] original_query``, valid as a derived table in the dialect. SQL Server accepts an
    ORDER BY there only together with OFFSET/TOP, so a selector that keeps its own order gets OFFSET 0 ROWS."""
    rules = DIALECT_RULES[dbms]
    if not rules.accepts_order_by_in_derived_table and selector_shape(query, dbms).keeps_own_order:
        query = f"{_without_terminator(query)} OFFSET 0 ROWS"
    alias = "AS original_query" if rules.accepts_as_before_subquery_alias else "original_query"
    return f"({query}) {alias}"


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
