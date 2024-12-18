# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.constants.attribute_constants import (
    ATTR_CONSTANT,
    ATTR_GENERATOR,
    ATTR_SCRIPT,
    ATTR_SOURCE,
    ATTR_TYPE,
    ATTR_VALUES,
)
from datamimic_ce.constants.element_constants import EL_ELEMENT
from datamimic_ce.contexts.context import Context
from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination
from datamimic_ce.statements.element_statement import ElementStatement
from datamimic_ce.tasks.key_variable_task import KeyVariableTask


class ElementTask(KeyVariableTask):
    def __init__(
        self,
        ctx: SetupContext,
        statement: ElementStatement,
        pagination: DataSourcePagination | None = None,
    ):
        super().__init__(ctx, statement, pagination)
        self._statement: ElementStatement = statement
        self._determine_generation_mode(ctx)

        if self._mode is None:
            raise ValueError(
                f"Must specify at least one attribute for element <{EL_ELEMENT}> '{self._statement.name}',"
                f" such as '{ATTR_SCRIPT}', '{ATTR_CONSTANT}', '{ATTR_VALUES}', "
                f"'{ATTR_GENERATOR}', '{ATTR_SOURCE} or '{ATTR_TYPE}'"
            )

    @property
    def statement(self) -> ElementStatement:
        return self._statement

    def execute(self, ctx: Context) -> None:
        pass

    def generate_xml_attribute(self, ctx: GenIterContext) -> dict:
        """
        Generate data for xml attribute
        :param ctx:
        :return:
        """
        from datamimic_ce.tasks.task_util import TaskUtil

        # check condition to enable or disable element, default True
        condition = TaskUtil.evaluate_condition_value(
            ctx=ctx, element_name=self._statement.name, value=self.statement.condition
        )

        if not condition:
            return {}

        value = self._generate_value(ctx)
        value = self._convert_generated_value(value)

        # Return new xml attribute
        return {f"@{self._statement.name}": value}
