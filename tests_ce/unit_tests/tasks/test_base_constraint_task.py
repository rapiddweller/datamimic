# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import unittest
from unittest.mock import MagicMock, patch

from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination
from datamimic_ce.statements.rule_statement import RuleStatement
from datamimic_ce.tasks.base_constraint_task import BaseConstraintTask


class ConcreteConstraintTask(BaseConstraintTask):
    """Concrete implementation of BaseConstraintTask for testing"""

    def execute(self, source_data, pagination=None, cyclic=False):
        if isinstance(source_data, GenIterContext):
            return self._process_geniter_context(source_data)

        data_list = list(source_data)
        for data_dict in data_list:
            self._convert_numeric_strings(data_dict)

        return self._apply_pagination(data_list, pagination, cyclic)


class TestBaseConstraintTask(unittest.TestCase):
    def setUp(self):
        # Create a mock statement with sub_statements
        self.mock_statement = MagicMock()
        self.mock_statement.sub_statements = []

        # Create concrete task for testing
        self.task = ConcreteConstraintTask(self.mock_statement)

    def test_convert_numeric_strings(self):
        # Test with various data types
        data = {
            "string": "hello",
            "int_string": "123",
            "negative_int_string": "-42",
            "float_string": "3.14",
            "negative_float_string": "-2.718",
            "already_int": 42,
            "already_float": 2.718,
            "bool": True,
            "none": None,
        }

        result = self.task._convert_numeric_strings(data)

        # Check conversions happened correctly
        self.assertEqual(result["string"], "hello")
        self.assertEqual(result["int_string"], 123)
        self.assertEqual(result["negative_int_string"], -42)
        self.assertEqual(result["float_string"], 3.14)
        self.assertEqual(result["negative_float_string"], -2.718)
        self.assertEqual(result["already_int"], 42)
        self.assertEqual(result["already_float"], 2.718)
        self.assertEqual(result["bool"], True)
        self.assertIsNone(result["none"])

    def test_handle_geniter_context(self):
        # Create a mock GenIterContext
        ctx = MagicMock(spec=GenIterContext)
        ctx.current_product = {"product_key": "product_value", "numeric": "42"}
        ctx.current_variables = {"var_key": "var_value", "pi": "3.14"}

        # Call the method
        result = self.task._handle_geniter_context(ctx)

        # Check that context data was extracted correctly
        self.assertEqual(result["product_key"], "product_value")
        self.assertEqual(result["var_key"], "var_value")
        self.assertEqual(result["numeric"], 42)  # Should be converted to int
        self.assertEqual(result["pi"], 3.14)  # Should be converted to float

    def test_apply_pagination_no_pagination(self):
        # Test without pagination
        data = [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}, {"id": 5}]

        result = self.task._apply_pagination(data, None, False)

        # Should return all data
        self.assertEqual(len(result), 5)
        self.assertEqual(result, data)

    def test_apply_pagination_with_pagination(self):
        # Test with pagination
        data = [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}, {"id": 5}]
        pagination = DataSourcePagination(skip=1, limit=2)

        result = self.task._apply_pagination(data, pagination, False)

        # Should return 2 items starting from index 1
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["id"], 2)
        self.assertEqual(result[1]["id"], 3)

    def test_apply_pagination_cyclic(self):
        # Test with cyclic behavior
        data = [{"id": 1}, {"id": 2}]
        pagination = DataSourcePagination(skip=0, limit=5)

        result = self.task._apply_pagination(data, pagination, True)

        # Should cycle through data to fill limit
        self.assertEqual(len(result), 5)
        self.assertEqual(result[0]["id"], 1)
        self.assertEqual(result[1]["id"], 2)
        self.assertEqual(result[2]["id"], 1)
        self.assertEqual(result[3]["id"], 2)
        self.assertEqual(result[4]["id"], 1)

    def test_process_geniter_context(self):
        # Create a rule statement
        rule_stmt = MagicMock(spec=RuleStatement)
        rule_stmt.if_rule = "True"
        rule_stmt.then_rule = "result = 42"

        # Add the rule to the mock statement
        self.mock_statement.sub_statements = [rule_stmt]

        # Create a mock GenIterContext
        ctx = MagicMock(spec=GenIterContext)
        ctx.current_product = {"some_value": 10}
        ctx.current_variables = {}

        # Mock the _execute_rule method to update locals_dict
        with patch.object(self.task, "_execute_rule") as mock_execute:
            # Simulate rule execution updating the dictionary
            def side_effect(rule, locals_dict, ctx=None):
                locals_dict["result"] = 42
                return locals_dict

            mock_execute.side_effect = side_effect

            # Process the context
            result_ctx = self.task._process_geniter_context(ctx)

            # Check that _execute_rule was called with the right arguments
            mock_execute.assert_called_once()
            self.assertEqual(mock_execute.call_args[0][0], rule_stmt)

            # Check that the context was returned
            self.assertEqual(result_ctx, ctx)


if __name__ == "__main__":
    unittest.main()
