# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.statements.item_statement import ItemStatement
from datamimic_ce.tasks.task import Task
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil


class ItemTask(Task):
    def __init__(
        self,
        ctx: SetupContext,
        statement: ItemStatement,
        class_factory_util: BaseClassFactoryUtil,
    ):
        self._statement = statement
        self._class_factory_util = class_factory_util

        # Not apply pagination for sub-statement
        self._sub_tasks = [
            class_factory_util.get_task_util_cls().get_task_by_statement(ctx, child_stmt)
            for child_stmt in statement.sub_statements
        ]

    @property
    def statement(self) -> ItemStatement:
        return self._statement

    def execute(self, parent_context: GenIterContext):
        """
        Generate data for element "item"
        :param parent_context:
        :return:
        """
        task_util_cls = self._class_factory_util.get_task_util_cls()

        # check condition to enable or disable element, default True
        condition = task_util_cls.evaluate_condition_value(
            ctx=parent_context,
            element_name=self._statement.name,
            value=self._statement.condition,
        )
        if condition:
            result = {}
            for sub_task in self._sub_tasks:
                ctx = GenIterContext(parent_context, "temp_item_name")
                # Create sub-context for each item generation
                # ItemTask generate product and apend to ctx.current_product
                sub_task.execute(ctx)
                # Add sub-element of item to result dict
                result.update(ctx.current_product)
            parent_context.add_current_product_field("temp_item_name", result)
