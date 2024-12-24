# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from datamimic_ce.constants.data_type_constants import DATA_TYPE_BOOL, DATA_TYPE_FLOAT, DATA_TYPE_INT, DATA_TYPE_STRING
from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.statements.array_statement import ArrayStatement
from datamimic_ce.tasks.task import Task


class ArrayTask(Task):
    def __init__(self, ctx: SetupContext | None, statement: ArrayStatement):
        self._valid_element_type = {
            DATA_TYPE_STRING,
            DATA_TYPE_INT,
            DATA_TYPE_BOOL,
            DATA_TYPE_FLOAT,
        }
        self._statement = statement

    @property
    def statement(self) -> ArrayStatement:
        return self._statement

    def execute(self, parent_context: GenIterContext) -> None:
        """
        Generate data for element "array"
        :param parent_context:
        :return: None
        """
        if self._statement.script:
            self._execute_script_generate(parent_context)
        else:
            self._execute_type_generate(parent_context)

    def _execute_type_generate(self, parent_context: GenIterContext) -> None:
        """
        Create new data for path
        """
        array_type = self._statement.type
        count = self.statement.count

        if not count:
            return None

        data_generation_util = parent_context.root.class_factory_util.get_data_generation_util()

        value: list[str | int | bool | float] = [
            data_generation_util.generate_random_value_based_on_type(array_type) for _ in range(count)
        ]
        # Add field "array" into current product
        parent_context.add_current_product_field(self._statement.name, value)

    def _execute_script_generate(self, parent_context: GenIterContext) -> None:
        """
        Create data from script value
        Result value datatype must be a List
        """
        valid_py_types = ["str", "int", "bool", "float"]

        if not self._statement.script:
            return None

        value = parent_context.evaluate_python_expression(self._statement.script)
        if isinstance(value, list):
            if len(value) > 0:
                # check validation of elements datatype
                element_type = type(value[0])
                element_type_name = element_type.__name__
                if element_type_name not in valid_py_types:
                    raise ValueError(
                        f"Failed while evaluate script '{self._statement.script} of <array> '{self._statement.name}':"
                        f"\n - expect array element datatypes in ({', '.join(valid_py_types)})"
                        f", but got invalid datatype '{element_type_name}'"
                    )
                if not all(isinstance(ele, element_type) for ele in value):
                    raise ValueError(
                        f"Failed while evaluate script '{self._statement.script} of <array> '{self._statement.name}':"
                        f"\n - all elements in list must be the same data type"
                    )
        else:
            raise ValueError(
                f"expect datatype list of evaluated script '{self._statement.script}'"
                f" of <array> '{self._statement.name}', but got invalid datatype '{type(value).__name__}'"
            )
        # Add field "array" into current product
        parent_context.add_current_product_field(self._statement.name, value)
