# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
from datamimic_ce.statements.rule_statement import RuleStatement
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil

from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.tasks.task import Task

from datamimic_ce.statements.constraints_statement import ConstraintsStatement


class ConstraintsTask(Task):
    def __init__(self, statement: ConstraintsStatement, class_factory_util: BaseClassFactoryUtil):
        self._statement = statement
        self._class_factory_util = class_factory_util

    @property
    def statement(self) -> ConstraintsStatement:
        return self._statement

    def execute(self, parent_context: GenIterContext):
        """
        Get condition from sub-tag Rule. Filter datas from context base on Rule
        """
        task_util_cls = self._class_factory_util.get_task_util_cls()
        child_stmt = [child_stmt for child_stmt in self.statement.sub_statements]
        for child_stmt in self.statement.sub_statements:
            if isinstance(child_stmt, RuleStatement):
                if_condition = parent_context.evaluate_python_expression(child_stmt.if_rule)
                if isinstance(if_condition, bool) and if_condition:
                    else_condition = parent_context.evaluate_python_expression(child_stmt.then_rule)
                    if isinstance(else_condition, bool) and else_condition is False:
                        parent_context.current_product = {}
                        # out of loop when remove the product
                        break
