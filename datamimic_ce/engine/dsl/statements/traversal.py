# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import logging

from datamimic_ce.engine.dsl.statements.base.composite_statement import CompositeStatement
from datamimic_ce.engine.dsl.statements.base.statement import Statement
from datamimic_ce.engine.dsl.statements.flow.branches.condition_statement import ConditionStatement
from datamimic_ce.engine.dsl.statements.generation.generate_statement import GenerateStatement
from datamimic_ce.engine.dsl.vocabulary.constants.convention_constants import NAME_SEPARATOR

logger = logging.getLogger("DATAMIMIC")


def get_nearest_generate_statement(statement: Statement) -> GenerateStatement | None:
    """Return the nearest enclosing generate; a generate itself has no enclosing result."""
    if isinstance(statement, GenerateStatement):
        return None

    parent_stmt = statement.parent_stmt
    while parent_stmt is not None:
        if isinstance(parent_stmt, GenerateStatement):
            return parent_stmt
        parent_stmt = parent_stmt.parent_stmt
    return None


def retrieve_sub_statement_by_fullname(statement: CompositeStatement, name: str) -> GenerateStatement | None:
    """Resolve a generate by its full name through executed conditional branches."""
    if not isinstance(statement, GenerateStatement):
        return None

    try:
        if name == statement.name:
            return statement

        segments = name.split(NAME_SEPARATOR)
        segments.pop(0)
        next_stmt_name = segments[0]
        name = NAME_SEPARATOR.join(segments)
        for sub_stmt in statement.sub_statements:
            if next_stmt_name == sub_stmt.name and isinstance(sub_stmt, CompositeStatement):
                return retrieve_sub_statement_by_fullname(sub_stmt, name)
            if isinstance(sub_stmt, CompositeStatement):
                condition_result = retrieve_executed_sub_gen_statement_by_name(sub_stmt, name)
                if condition_result:
                    return condition_result
    except IndexError as error:
        logger.error(f"Error when retrieve sub statement by fullname '{name}': {error}")
    return None


def retrieve_executed_sub_gen_statement_by_name(
    statement: CompositeStatement, name: str
) -> GenerateStatement | None:
    """Resolve a generate through branches recorded as executed by a condition."""
    if not isinstance(statement, ConditionStatement):
        return None

    if statement.executed_statements:
        stmt_name = name.split(NAME_SEPARATOR)[0]
        for executed_statement in statement.executed_statements:
            for sub_statement in executed_statement.sub_statements:
                if stmt_name == sub_statement.name and isinstance(sub_statement, CompositeStatement):
                    return retrieve_sub_statement_by_fullname(sub_statement, name)
                if isinstance(sub_statement, ConditionStatement):
                    result_statement = retrieve_executed_sub_gen_statement_by_name(sub_statement, name)
                    if result_statement:
                        return result_statement
    else:
        logger.error(
            f"Error when retrieve sub statement: "
            f"Can't retrieve '{statement.name}' of `<condition>` because it didn't execute any element"
        )
    return None
