# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.contexts.context import Context
from datamimic_ce.domains.common.literal_generators.generator_util import GeneratorUtil
from datamimic_ce.statements.generator_statement import GeneratorStatement
from datamimic_ce.tasks.task import SetupSubTask


class GeneratorTask(SetupSubTask):
    """
    Store a generator to SetupContext
    """

    def __init__(self, statement: GeneratorStatement):
        self._statement = statement

    @property
    def statement(self) -> GeneratorStatement:
        return self._statement

    def execute(self, ctx: Context):
        # Creation and optional caching of the generator is delegated to
        # ``GeneratorUtil``. It decides whether the generator should be stored
        # in the root context based on the generator's ``cache_in_root`` flag.
        GeneratorUtil(ctx).create_generator(self._statement.generator, self._statement, key=self._statement.name)
