# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.statements.while_statement import WhileStatement
from datamimic_ce.tasks.condition_task import ConditionTask
from datamimic_ce.tasks.task import CommonSubTask, GenSubTask


class WhileTask(GenSubTask):
    """Repeat the child statements while ``condition`` holds (evaluated against the current row).

    The body must mutate a value visible to the condition (a <variable>/namespace update, or a <key>
    read via its name) — otherwise the condition never changes and the loop is infinite. A mandatory
    ``max_iterations`` cap RAISES rather than silently stopping, so a non-terminating loop surfaces as
    an error instead of masking a defect.
    """

    def __init__(self, statement: WhileStatement):
        self._statement = statement

    @property
    def statement(self) -> WhileStatement:
        return self._statement

    def execute(self, parent_context: GenIterContext) -> None:
        from datamimic_ce.tasks.generate_task import GenerateTask
        from datamimic_ce.tasks.task_util import TaskUtil

        child_tasks = [
            TaskUtil.get_task_by_statement(ctx=parent_context.root, stmt=child_stmt)
            for child_stmt in self._statement.sub_statements
        ]

        iterations = 0
        while parent_context.evaluate_python_expression(self._statement.condition):
            if iterations >= self._statement.max_iterations:
                raise ValueError(
                    f"<while> exceeded max_iterations={self._statement.max_iterations}: condition "
                    f"'{self._statement.condition}' never became false (possible infinite loop)"
                )
            # Side-effect loop: the body's <key>/<variable> mutate the row (current_product/variables),
            # so re-executing them per iteration advances the condition. Results are not accumulated.
            for child_task in child_tasks:
                if not isinstance(child_task, GenerateTask | ConditionTask | GenSubTask | CommonSubTask):
                    raise ValueError(f"Unexpected sub-task in <while>: {type(child_task)}")
                child_task.execute(parent_context)
            iterations += 1
