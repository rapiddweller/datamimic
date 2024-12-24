# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from abc import ABC

from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.statements.else_if_statement import ElseIfStatement
from datamimic_ce.statements.else_statement import ElseStatement
from datamimic_ce.statements.if_statement import IfStatement
from datamimic_ce.tasks.condition_task import ConditionTask
from datamimic_ce.tasks.generate_task import GenerateTask
from datamimic_ce.tasks.task import Task
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil


class IfElseBaseTask(Task, ABC):
    def __init__(
        self,
        statement: IfStatement | ElseIfStatement | ElseStatement,
        class_factory_util: BaseClassFactoryUtil,
    ):
        self._statement = statement
        self._class_factory_util = class_factory_util

    @property
    def statement(self) -> IfStatement | ElseIfStatement | ElseStatement:
        return self._statement

    def execute(self, parent_context: GenIterContext):
        """
        Generate data for element "if", "else_if" and "else"
        :param parent_context:
        :return:
        """
        task_util_cls = self._class_factory_util.get_task_util_cls()
        child_tasks = [
            task_util_cls.get_task_by_statement(ctx=parent_context.root, stmt=child_stmt)
            for child_stmt in self.statement.sub_statements
        ]

        # store statement of executed task to parent statement (condition statement) for later use
        if self._statement.parent_stmt is not None and hasattr(self._statement.parent_stmt, "add_executed_statement"):
            self._statement.parent_stmt.add_executed_statement(self.statement)

        product_holder: dict = {}
        for child_task in child_tasks:
            # Add generate product to current product_holder
            if isinstance(child_task, GenerateTask | ConditionTask):
                # Execute sub generate task
                values = child_task.execute(parent_context)
                if isinstance(values, dict):
                    for key, value in values.items():
                        product_holder[key] = product_holder.get(key, []) + value
            else:
                child_task.execute(parent_context)
        return product_holder
