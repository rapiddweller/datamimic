# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
import logging
from abc import ABC, abstractmethod
from typing import Any

from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination
from datamimic_ce.services.data_transformation_service import DataTransformationService
from datamimic_ce.services.rule_execution_service import RuleExecutionService
from datamimic_ce.statements.composite_statement import CompositeStatement
from datamimic_ce.statements.rule_statement import RuleStatement
from datamimic_ce.tasks.task import Task

logger = logging.getLogger("datamimic")


class BaseConstraintTask(Task, ABC):
    """
    Base class for all constraint-related tasks (mapping, source constraints, target constraints).

    This class extracts and centralizes common functionality across all constraint tasks:
    - Type conversion methods
    - Context handling
    - Rule execution logic
    - Error handling and logging
    - Data list processing
    """

    def __init__(self, statement: CompositeStatement):
        self._statement = statement

    @property
    def statement(self) -> CompositeStatement:
        return self._statement

    def _convert_numeric_strings(self, data_dict: dict[str, Any]) -> dict[str, Any]:
        """
        Helper function to convert string values to numeric types where appropriate.

        Args:
            data_dict: Dictionary containing values to be converted

        Returns:
            Dictionary with string values converted to appropriate numeric types
        """
        return DataTransformationService.convert_numeric_strings(data_dict)

    def _handle_geniter_context(self, ctx: GenIterContext) -> dict[str, Any]:
        """
        Extract data from GenIterContext and prepare locals_dict for rule evaluation.

        Args:
            ctx: The GenIterContext containing current product and variables

        Returns:
            Dictionary containing variables to be used in rule evaluation
        """
        # Use ctx's current_product and current_variables as local variables for eval
        # Ensure we have a proper dictionary even if the context is empty
        locals_dict = {}
        if hasattr(ctx, "current_product") and ctx.current_product is not None:
            try:
                locals_dict.update(ctx.current_product)
            except (TypeError, ValueError) as e:
                logger.warning(f"Could not update locals_dict with current_product: {e}")
        if hasattr(ctx, "current_variables") and ctx.current_variables is not None:
            try:
                locals_dict.update(ctx.current_variables)
            except (TypeError, ValueError) as e:
                logger.warning(f"Could not update locals_dict with current_variables: {e}")

        # Ensure we have a valid locals_dict for evaluation
        if not locals_dict:
            # If no data available, create a minimal dictionary
            locals_dict = {"_empty": True}

        # Convert string values to numeric types where appropriate
        locals_dict = self._convert_numeric_strings(locals_dict)

        return locals_dict

    def _execute_rule(
        self, rule_statement: RuleStatement, locals_dict: dict[str, Any], ctx: GenIterContext | None = None
    ) -> dict[str, Any]:
        """
        Execute a single rule with error handling.

        Args:
            rule_statement: The rule to execute
            locals_dict: Dictionary containing variables for rule evaluation
            ctx: Optional GenIterContext to update with results (for generate workflow)

        Returns:
            Updated locals_dict with any changes made by rule execution
        """
        task_name = self.__class__.__name__

        if ctx is not None:
            return RuleExecutionService.execute_rule_for_ctx(
                rule_statement=rule_statement, locals_dict=locals_dict, ctx=ctx, rule_owner=task_name
            )
        else:
            # Execute for regular dictionary without GenIterContext
            updated_dict, _ = RuleExecutionService.execute_rule_for_dict(
                rule_statement=rule_statement, data_dict=locals_dict, rule_owner=task_name
            )
            return updated_dict

    def _process_geniter_context(self, ctx: GenIterContext) -> GenIterContext:
        """
        Process a GenIterContext by executing all rules against it.

        Args:
            ctx: The GenIterContext to process

        Returns:
            Updated GenIterContext after rule execution
        """
        # Prepare locals_dict from context
        locals_dict = self._handle_geniter_context(ctx)

        # Execute all rules against the context
        for child_stmt in self.statement.sub_statements:
            if isinstance(child_stmt, RuleStatement):
                locals_dict = self._execute_rule(child_stmt, locals_dict, ctx)

        return ctx

    def _apply_pagination(
        self, data_list: list[Any], pagination: DataSourcePagination | None, cyclic: bool
    ) -> list[Any]:
        """
        Apply pagination and cyclic behavior to the processed data.

        Args:
            data_list: List of data items to paginate
            pagination: Optional pagination configuration
            cyclic: Whether to cycle through the data

        Returns:
            Paginated (and possibly cycled) data
        """
        return DataTransformationService.apply_pagination(data_list, pagination, cyclic)

    def _process_data_with_rules(
        self, data_list: list[dict[str, Any]], filter_mode: bool = True
    ) -> list[dict[str, Any]]:
        """
        Process a list of dictionaries by applying rules from the statement.

        Args:
            data_list: List of dictionaries to process
            filter_mode: Whether to filter out items that don't meet rules (True) or just transform them (False)

        Returns:
            Processed list of dictionaries
        """
        return DataTransformationService.process_data_with_rules(
            data_list=data_list, statement=self.statement, rule_owner=self.__class__.__name__, filter_mode=filter_mode
        )

    def _handle_standard_execution(
        self,
        source_data,
        pagination: DataSourcePagination | None = None,
        cyclic: bool | None = False,
        filter_mode: bool = True,
    ) -> list[Any] | GenIterContext:
        """
        Standard execution flow for constraint tasks.

        Args:
            source_data: The source data to be processed
            pagination: Optional pagination configuration
            cyclic: Whether to cycle through the source data
            filter_mode: Whether to filter out items that don't meet rules

        Returns:
            Processed data or updated GenIterContext
        """
        # Handle GenIterContext case (integration with generate workflow)
        if isinstance(source_data, GenIterContext):
            return self._process_geniter_context(source_data)

        # Handle regular data flow for source data as a list
        result_data = list(source_data)

        # If source is empty, return empty list
        if len(result_data) == 0:
            return []

        # Process the data with rules
        result_data = self._process_data_with_rules(result_data, filter_mode)

        # Apply pagination and return the result
        return self._apply_pagination(result_data, pagination, cyclic or False)

    @abstractmethod
    def execute(
        self, source_data, pagination: DataSourcePagination | None = None, cyclic: bool | None = False
    ) -> list[Any] | GenIterContext:
        """
        Execute the constraint task.

        This method must be implemented by subclasses to define their specific behavior.

        Args:
            source_data: The source data to be processed
            pagination: Optional pagination configuration
            cyclic: Whether to cycle through the source data

        Returns:
            Processed data or updated GenIterContext
        """
        pass
