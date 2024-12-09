# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/


from datamimic_ce.constants.convention_constants import NAME_SEPARATOR
from datamimic_ce.logger import logger
from datamimic_ce.statements.composite_statement import CompositeStatement
from datamimic_ce.statements.else_if_statement import ElseIfStatement
from datamimic_ce.statements.else_statement import ElseStatement
from datamimic_ce.statements.generate_statement import GenerateStatement
from datamimic_ce.statements.if_statement import IfStatement


class ConditionStatement(CompositeStatement):
    def __init__(self, parent_stmt: CompositeStatement):
        super().__init__(name=None, parent_stmt=parent_stmt)
        self._executed_statements = set()

    def add_executed_statement(self, value: IfStatement | ElseIfStatement | ElseStatement):
        """
        Keep executed statements for later use
        """
        self._executed_statements.add(value)

    def retrieve_executed_sub_gen_statement_by_name(self, name) -> "GenerateStatement":
        """
        Retrieve sub GenerateStatement by statement fullname
        :param name: full path name from <condition> parent to searching statement short name.
                    For example, search for `people` generate, which is
                    sub-statement of `container` generate (container stmt > condition stmt > if stmt > people stmt)
                    then name will be `container|people`
        """
        if self._executed_statements:
            stmt_name = name.split(NAME_SEPARATOR)[0]
            for executed_statement in self._executed_statements:
                # search in sub_statements of each condition executed task statements
                for sub_statement in executed_statement.sub_statements:
                    if stmt_name == sub_statement.name and isinstance(sub_statement, GenerateStatement):
                        return sub_statement.retrieve_sub_statement_by_fullname(name)
                    elif isinstance(sub_statement, ConditionStatement):
                        result_statement = sub_statement.retrieve_executed_sub_gen_statement_by_name(name)
                        # only return when have result_statement, otherwise continue looping
                        if result_statement:
                            return result_statement
        else:
            logger.error(
                f"Error when retrieve sub statement: "
                f"Can't retrieve '{self.name}' of `<condition>` because it didn't execute any element"
            )
        return None
