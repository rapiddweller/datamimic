# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.engine.dsl.api import (
    ATTR_CONSTANT,
    ATTR_GENERATOR,
    ATTR_SCRIPT,
    ATTR_SOURCE,
    ATTR_TYPE,
    ATTR_VALUES,
    EL_KEY,
    CompositeStatement,
    KeyStatement,
)
from datamimic_ce.engine.io.api import DataSourcePagination
from datamimic_ce.engine.runtime.contexts.context import Context, SetupContext
from datamimic_ce.engine.runtime.contexts.geniter_context import GenIterContext
from datamimic_ce.engine.runtime.scripting.evaluation import evaluate_condition_value
from datamimic_ce.engine.runtime.tasks.base.dispatch import create_task
from datamimic_ce.engine.runtime.tasks.base.task import GenSubTask
from datamimic_ce.engine.runtime.tasks.values.construction.factory import GeneratorUtil
from datamimic_ce.engine.runtime.tasks.values.key_variable_task import KeyVariableTask
from datamimic_ce.engine.runtime.tasks.values.scalar.element_task import ElementTask


class KeyTask(KeyVariableTask, GenSubTask):
    def __init__(
        self,
        ctx: SetupContext,
        statement: KeyStatement,
        pagination: DataSourcePagination | None = None,
    ):
        super().__init__(ctx, statement, pagination)
        self._statement: KeyStatement = statement
        self._determine_generation_mode(ctx)

        if self._mode is None:
            raise ValueError(
                f"Must specify at least one attribute for element <{EL_KEY}> '{self._statement.name}',"
                f" such as '{ATTR_SCRIPT}', '{ATTR_CONSTANT}', '{ATTR_VALUES}', "
                f"'{ATTR_GENERATOR}', '{ATTR_SOURCE} or '{ATTR_TYPE}'"
            )

    def pre_execute(self, ctx: Context):
        if self.statement.generator is not None and "SequenceTableGenerator" in self.statement.generator:
            sequence_table_generator = GeneratorUtil(ctx).create_generator(
                str(self._statement.generator), self._statement, self._pagination
            )
            sequence_table_generator.pre_execute(ctx)

    @property
    def statement(self) -> KeyStatement:
        return self._statement

    def execute(self, ctx: Context) -> None:
        """
        Generate data for element "attribute"
        If 'type' element is not specified, then default type of generated data is string
        :param ctx:
        :return:
        """
        root_ctx = ctx.root

        # check condition to enable or disable element, default True
        condition = evaluate_condition_value(ctx, self._statement.name, self.statement.condition)

        if condition:
            if self.statement.null_quota and ctx.rng.random() < self.statement.null_quota:
                value = None
            else:
                value = self._generate_value(ctx)
                value = self._convert_generated_value(value)

            attributes = {}
            if isinstance(self._statement, CompositeStatement):
                for stmt in self._statement.sub_statements:
                    task = create_task(stmt, root_ctx)
                    if isinstance(task, ElementTask) and isinstance(ctx, GenIterContext):
                        attributes.update(task.generate_xml_attribute(ctx))
                    else:
                        raise ValueError(
                            f"Cannot execute subtask {task.__class__.__name__} of <key> '{self.statement.name}'"
                        )

            result = value if len(attributes) == 0 else {"#text": value, **attributes}
            # Add field "attribute" into current product
            if isinstance(ctx, GenIterContext):
                ctx.add_current_product_field(self._statement.name, result)
        elif self.statement.default_value is not None:
            # If condition false and default_value exist, assign default value to key
            default_value = ctx.evaluate_python_expression(self.statement.default_value)
            if isinstance(ctx, GenIterContext):
                ctx.add_current_product_field(self._statement.name, default_value)
