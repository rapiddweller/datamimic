# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import unittest
from unittest.mock import MagicMock, patch

from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.services.rule_execution_service import RuleExecutionService
from datamimic_ce.statements.rule_statement import RuleStatement


class TestRuleExecutionService(unittest.TestCase):
    """Unit tests for RuleExecutionService"""

    def setUp(self):
        # Mock logger to prevent actual logging during tests
        self.patcher = patch("datamimic_ce.services.rule_execution_service.logger")
        self.mock_logger = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_evaluate_condition_true(self):
        # Test with a condition that evaluates to True
        rule = MagicMock(spec=RuleStatement)
        rule.if_rule = "x > 5"

        locals_dict = {"x": 10}

        result = RuleExecutionService.evaluate_condition(rule, locals_dict)

        self.assertTrue(result)

    def test_evaluate_condition_false(self):
        # Test with a condition that evaluates to False
        rule = MagicMock(spec=RuleStatement)
        rule.if_rule = "x > 5"

        locals_dict = {"x": 3}

        result = RuleExecutionService.evaluate_condition(rule, locals_dict)

        self.assertFalse(result)

    def test_evaluate_condition_error(self):
        # Test with a condition that raises an error
        rule = MagicMock(spec=RuleStatement)
        rule.if_rule = "x.undefined_method()"

        locals_dict = {"x": 10}

        result = RuleExecutionService.evaluate_condition(rule, locals_dict)

        # Should return False and log the error
        self.assertFalse(result)
        self.mock_logger.warning.assert_called_once()

    def test_execute_rule_for_ctx_evaluation(self):
        # Test executing a rule that evaluates an expression
        rule = MagicMock(spec=RuleStatement)
        rule.if_rule = "x > 5"
        rule.then_rule = "x * 2"

        locals_dict = {"x": 10}
        ctx = MagicMock(spec=GenIterContext)

        result_dict = RuleExecutionService.execute_rule_for_ctx(rule, locals_dict, ctx)

        # Should call add_current_product_field with the key from the assignment
        self.assertEqual(result_dict, locals_dict)

    def test_execute_rule_for_ctx_assignment(self):
        # Test executing a rule with an assignment
        rule = MagicMock(spec=RuleStatement)
        rule.if_rule = "x > 5"
        rule.then_rule = "y = x * 2"

        locals_dict = {"x": 10}
        ctx = MagicMock(spec=GenIterContext)

        result_dict = RuleExecutionService.execute_rule_for_ctx(rule, locals_dict, ctx)

        # Should update locals_dict with the new value
        self.assertEqual(result_dict["y"], 20)
        # Should call add_current_product_field
        ctx.add_current_product_field.assert_called_with("y", 20)

    def test_execute_rule_for_ctx_statement(self):
        # Test executing a rule with a multi-line statement
        rule = MagicMock(spec=RuleStatement)
        rule.if_rule = "x > 5"
        rule.then_rule = "y = x * 2\nz = y + 5"

        locals_dict = {"x": 10}
        ctx = MagicMock(spec=GenIterContext)

        result_dict = RuleExecutionService.execute_rule_for_ctx(rule, locals_dict, ctx)

        # Should update locals_dict with all new values
        self.assertEqual(result_dict["y"], 20)
        self.assertEqual(result_dict["z"], 25)
        # Should call add_current_product_field for each new value
        ctx.add_current_product_field.assert_any_call("y", 20)
        ctx.add_current_product_field.assert_any_call("z", 25)

    def test_execute_rule_for_ctx_boolean_false(self):
        # Test executing a rule that returns boolean False
        rule = MagicMock(spec=RuleStatement)
        rule.if_rule = "x > 5"
        rule.then_rule = "False"

        locals_dict = {"x": 10}
        ctx = MagicMock(spec=GenIterContext)

        result_dict = RuleExecutionService.execute_rule_for_ctx(rule, locals_dict, ctx)

        # Should mark record for filtering
        ctx.add_current_product_field.assert_called_with("_filtered", True)

    def test_execute_rule_for_dict_boolean_false(self):
        # Test executing a rule that returns boolean False for a dictionary
        rule = MagicMock(spec=RuleStatement)
        rule.if_rule = "x > 5"
        rule.then_rule = "False"

        data_dict = {"x": 10}

        result_dict, should_filter = RuleExecutionService.execute_rule_for_dict(rule, data_dict)

        # Should flag record for filtering
        self.assertTrue(should_filter)

    def test_execute_rule_for_dict_assignment(self):
        # Test executing a rule with an assignment for a dictionary
        rule = MagicMock(spec=RuleStatement)
        rule.if_rule = "x > 5"
        rule.then_rule = "y = x * 2"

        data_dict = {"x": 10}

        result_dict, should_filter = RuleExecutionService.execute_rule_for_dict(rule, data_dict)

        # Should update the dictionary with new value
        self.assertEqual(result_dict["y"], 20)
        # Should not flag for filtering
        self.assertFalse(should_filter)


if __name__ == "__main__":
    unittest.main()
