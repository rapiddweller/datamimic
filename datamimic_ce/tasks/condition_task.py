# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.statements.condition_statement import ConditionStatement
from datamimic_ce.statements.else_if_statement import ElseIfStatement
from datamimic_ce.statements.else_statement import ElseStatement
from datamimic_ce.statements.if_statement import IfStatement
from datamimic_ce.tasks.task import GenSubTask


class ConditionTask(GenSubTask):
    def __init__(self, statement: ConditionStatement):
        self._statement = statement

    @property
    def statement(self) -> ConditionStatement:
        return self._statement

    def execute(self, parent_context: GenIterContext) -> None | dict:
        """
        Generate data for element "condition"
        :param parent_context:
        :return:
        """
        from datamimic_ce.tasks.task_util import TaskUtil

        child_tasks = [
            TaskUtil.get_task_by_statement(parent_context.root, child_stmt)
            for child_stmt in self.statement.sub_statements
        ]

        result = None

        # Check if any stmt block is executed
        is_executed = False
        for child_task in child_tasks:
            # If the stmt block is executed, break the loop
            if not isinstance(child_task, GenSubTask):
                raise ValueError(f"Generate sub-task expected, but got {type(child_task)}")
            if is_executed:
                break
            child_stmt = child_task.statement
            if isinstance(child_stmt, IfStatement | ElseIfStatement):
                # Get the condition from the child task's statement
                condition = parent_context.evaluate_python_expression(child_stmt.condition)
                if condition:
                    result = child_task.execute(parent_context)
                    is_executed = True
            elif isinstance(child_stmt, ElseStatement):
                result = child_task.execute(parent_context)
                is_executed = True

        if isinstance(result, dict):
            return result
        else:
            return None
