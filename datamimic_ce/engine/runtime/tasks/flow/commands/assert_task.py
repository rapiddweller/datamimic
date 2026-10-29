# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.engine.dsl.api import AssertStatement
from datamimic_ce.engine.runtime.contexts.context import Context
from datamimic_ce.engine.runtime.tasks.base.task import CommonSubTask
from datamimic_ce.errors import DescriptorLocation, DomainError, IssueCode, UserErrorBase, task_config_error


class AssertTask(CommonSubTask):
    """Fail the run when ``condition`` does not evaluate truthy.

    Conditions run per record inside <generate> and once under <setup>.
    Failures retain explicit user messages without automatically dumping record values.
    """

    def __init__(self, statement: AssertStatement):
        self._statement = statement

    @property
    def statement(self) -> AssertStatement:
        return self._statement

    def _location(self) -> DescriptorLocation:
        # Built only on a failure: an assert runs for every row, and the location reads the current descriptor name.
        return DescriptorLocation("assert", attribute="condition", line=self._statement.line)

    def execute(self, ctx: Context) -> None:
        condition = self._statement.condition
        try:
            passed = bool(ctx.evaluate_python_expression(condition))
        except (UserErrorBase, DomainError) as error:
            if isinstance(error, UserErrorBase) and error.location is None:
                error.location = self._location()
            raise
        except Exception as err:
            # A broken expression (typo'd field, syntax error) must name the assert, not surface
            # as a bare NameError from deep inside the evaluator.
            raise task_config_error(
                code=IssueCode.TASK_EXPRESSION_EVAL_FAILED,
                expr="assert.condition",
                error="assert expression failed",
                location=self._location(),
            ) from err
        if passed:
            return
        statement = self._statement
        extra = (
            f" | {statement.message}"
            if statement.message is not None
            else f" | The message of the <assert> at line {statement.line} is not shown: it contains {{, }} or __ "
            "and can hold a property value"
            if statement.message_hidden
            else ""
        )
        raise task_config_error(
            code=IssueCode.TASK_ASSERT_FAILED,
            condition="configured condition",
            extra=extra,
            location=self._location(),
        )
