# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.statements.list_statement import ListStatement
from datamimic_ce.tasks.task import GenSubTask
from datamimic_ce.tasks.task_util import TaskUtil


class ListTask(GenSubTask):
    def __init__(
        self,
        ctx: SetupContext,
        statement: ListStatement,
    ):
        self._statement = statement
        # Not apply pagination for sub-statement
        self._item_tasks = [TaskUtil.get_task_by_statement(ctx, child_stmt) for child_stmt in statement.sub_statements]
        self._converter_list = TaskUtil.create_converter_list(ctx, self._statement.converter)

    @property
    def statement(self) -> ListStatement:
        return self._statement

    def execute(self, parent_context: GenIterContext):
        """
        Generate data for element "list"
        :param parent_context:
        :return:
        """
        value = []
        for item_task in self._item_tasks:
            if self.statement.name is None:
                raise ValueError(
                    "Statement name is missing. This could happen if the ListStatement "
                    "object was initialized without a name. Ensure that 'statement.name' "
                    "is set before calling execute()."
                )
            ctx = GenIterContext(parent_context, self.statement.name)
            # Create sub-context for each item generation
            # ItemTask generate product and append to ctx.current_product
            if not isinstance(item_task, GenSubTask):
                raise ValueError(f"Generate sub-task expected, but got {type(item_task)}")
            item_task.execute(ctx)
            # Add current_product value of item to list
            value.append(ctx.current_product.get("temp_item_name"))
        for converter in self._converter_list:
            value = converter.convert(value)
        parent_context.add_current_product_field(self._statement.name, value)
