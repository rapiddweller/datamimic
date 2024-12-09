# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/

from datamimic_ce.contexts.context import Context
from datamimic_ce.generators.generator_util import GeneratorUtil
from datamimic_ce.statements.generator_statement import GeneratorStatement
from datamimic_ce.tasks.task import Task


class GeneratorTask(Task):
    """
    Store a generator to SetupContext
    """

    def __init__(self, statement: GeneratorStatement):
        self._statement = statement

    @property
    def statement(self) -> GeneratorStatement:
        return self._statement

    def execute(self, ctx: Context):
        # Store a generator to SetupContext
        ctx.root.generators[self._statement.name] = GeneratorUtil(ctx).create_generator(
            self._statement.generator, self._statement
        )
