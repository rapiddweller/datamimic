# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
import logging
from typing import Any

from datamimic_ce.contexts.context import SAFE_GLOBALS
from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.statements.rule_statement import RuleStatement

logger = logging.getLogger("datamimic")


class RuleExecutionService:
    """
    Service for executing rule statements with consistent error handling and result processing.

    This service centralizes the rule execution logic, making it available to any component that needs
    to execute rules, not just constraint tasks.
    """

    @staticmethod
    def evaluate_condition(rule_statement: RuleStatement, locals_dict: dict[str, Any]) -> bool:
        """
        Evaluate the if-condition of a rule statement.

        Args:
            rule_statement: The rule statement containing the condition
            locals_dict: Dictionary of variables available for evaluation

        Returns:
            True if the condition evaluates to True, False otherwise
        """
        try:
            if_condition = eval(rule_statement.if_rule, SAFE_GLOBALS, locals_dict)
            return isinstance(if_condition, bool) and if_condition
        except Exception as e:
            logger.warning(f"Error evaluating condition '{rule_statement.if_rule}': {e}")
            return False

    @staticmethod
    def execute_rule_for_ctx(
        rule_statement: RuleStatement,
        locals_dict: dict[str, Any],
        ctx: GenIterContext,
        rule_owner: str = "RuleExecutionService",
    ) -> dict[str, Any]:
        """
        Execute a rule for a GenIterContext and update the context with the results.

        Args:
            rule_statement: The rule statement to execute
            locals_dict: Dictionary of variables available for evaluation
            ctx: The GenIterContext to update with results
            rule_owner: Name of the component executing the rule (for logging)

        Returns:
            Updated locals_dict after rule execution
        """
        if not RuleExecutionService.evaluate_condition(rule_statement, locals_dict):
            return locals_dict

        try:
            # Try to handle as boolean condition first
            try:
                # Execute then_rule and update the current product with results
                result = eval(rule_statement.then_rule, SAFE_GLOBALS, locals_dict)

                # If it's a boolean and False, skip this record
                if isinstance(result, bool) and result is False:
                    # Mark product for potential filtering in higher-level code
                    ctx.add_current_product_field("_filtered", True)
                # If it's an assignment (key=value), extract the key and value
                elif "=" in rule_statement.then_rule and "==" not in rule_statement.then_rule:
                    key = rule_statement.then_rule.split("=")[0].strip()
                    ctx.add_current_product_field(key, result)
                    # Update locals_dict for subsequent evaluations
                    locals_dict[key] = result
            except SyntaxError:
                # If it's an assignment, execute it
                # Create a copy of locals_dict to track changes
                old_locals = locals_dict.copy()
                exec(rule_statement.then_rule, SAFE_GLOBALS, locals_dict)
                # Update ctx with any new or changed values
                for key, value in locals_dict.items():
                    if key not in old_locals or old_locals[key] != value and not key.startswith("_"):
                        ctx.add_current_product_field(key, value)
        except Exception as e:
            logger.warning(f"Error executing rule in {rule_owner}: {e}")

        return locals_dict

    @staticmethod
    def execute_rule_for_dict(
        rule_statement: RuleStatement, data_dict: dict[str, Any], rule_owner: str = "RuleExecutionService"
    ) -> tuple[dict[str, Any], bool]:
        """
        Execute a rule for a dictionary and return the updated dictionary and a flag indicating
        if the record should be filtered.

        Args:
            rule_statement: The rule statement to execute
            data_dict: Dictionary to execute the rule against
            rule_owner: Name of the component executing the rule (for logging)

        Returns:
            Tuple containing (updated data_dict, should_filter_record)
        """
        should_filter = False

        if not RuleExecutionService.evaluate_condition(rule_statement, data_dict):
            return data_dict, should_filter

        try:
            # Try to execute the then_rule as a boolean expression first
            try:
                else_condition = eval(rule_statement.then_rule, SAFE_GLOBALS, data_dict)
                # If it's a boolean and False, flag for filtering
                if isinstance(else_condition, bool) and else_condition is False:
                    should_filter = True
            except SyntaxError:
                # If the then_rule is an assignment, execute it
                exec(rule_statement.then_rule, SAFE_GLOBALS, data_dict)
        except Exception as e:
            logger.warning(f"Error executing rule in {rule_owner}: {e}")

        return data_dict, should_filter
