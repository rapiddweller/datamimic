# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.contexts.context import Context
from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.statements.assert_statement import AssertStatement
from datamimic_ce.tasks.task import CommonSubTask


class AssertTask(CommonSubTask):
    """Fail the run when ``condition`` does not evaluate truthy.

    Inside a <generate> the condition sees the current record's fields/variables (checked per record);
    under <setup> it sees the setup context (checked once). The failure names the condition, the
    user message and — when available — the offending record, so a violated data invariant surfaces
    as a hard error instead of silently wrong output.
    """

    def __init__(self, statement: AssertStatement):
        self._statement = statement

    @property
    def statement(self) -> AssertStatement:
        return self._statement

    def execute(self, ctx: Context) -> None:
        condition = self._statement.condition
        if bool(ctx.evaluate_python_expression(condition)):
            return
        parts = [f"<assert> failed: condition '{condition}' is not true"]
        if self._statement.message:
            parts.append(self._statement.message)
        if isinstance(ctx, GenIterContext) and ctx.current_product:
            parts.append(f"record: {ctx.current_product}")
        raise ValueError(" | ".join(parts))
