# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import re

from datamimic_ce.contexts.context import Context
from datamimic_ce.logger import logger
from datamimic_ce.statements.echo_statement import EchoStatement
from datamimic_ce.tasks.task import Task


class EchoTask(Task):
    """
    Print value inside echo tag to debug logger
    """

    def __init__(self, statement: EchoStatement):
        self._statement = statement

    def execute(self, ctx: Context):
        _value = self.statement.value
        #  check _value contain {} or not, evaluate data if true
        if re.search(r"{.*?}", _value):
            # if _value contain ' or " then add escaped character before it
            escaped_text = _value.replace("'", "\\'").replace('"', '\\"')
            # evaluate echo value before logging
            evaluated_value = ctx.evaluate_python_expression(f"f'{escaped_text}'")
            logger.debug(f"Echo - {evaluated_value}")
        else:
            logger.debug(f"Echo - {_value}")

    @property
    def statement(self) -> EchoStatement:
        return self._statement
