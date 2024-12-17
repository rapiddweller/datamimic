# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.statements.condition_statement import ConditionStatement
from datamimic_ce.statements.else_if_statement import ElseIfStatement
from datamimic_ce.statements.else_statement import ElseStatement
from datamimic_ce.statements.if_statement import IfStatement
from datamimic_ce.tasks.task import Task
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil


class ConditionTask(Task):
    def __init__(self, statement: ConditionStatement, class_factory_util: BaseClassFactoryUtil):
        self._statement = statement
        self._class_factory_util = class_factory_util

    @property
    def statement(self) -> ConditionStatement:
        return self._statement

    def execute(self, parent_context: GenIterContext) -> None | dict:
        """
        Generate data for element "condition"
        :param parent_context:
        :return:
        """
        task_util_cls = self._class_factory_util.get_task_util_cls()
        child_tasks = [
            task_util_cls.get_task_by_statement(ctx=parent_context.root, stmt=child_stmt)
            for child_stmt in self.statement.sub_statements
        ]

        result = None

        # Check if any stmt block is executed
        is_executed = False
        for child_task in child_tasks:
            # If the stmt block is executed, break the loop
            if is_executed:
                break
            if isinstance(child_task.statement, IfStatement | ElseIfStatement):
                # Get the condition from the child task's statement
                condition = parent_context.evaluate_python_expression(child_task.statement.condition)
                if condition:
                    result = child_task.execute(parent_context)
                    is_executed = True
            elif isinstance(child_task.statement, ElseStatement):
                result = child_task.execute(parent_context)
                is_executed = True

        if isinstance(result, dict):
            return result
        else:
            return None
