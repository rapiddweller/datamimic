# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
import logging
from typing import Any

from datamimic_ce.contexts.context import DotableDict
from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination
from datamimic_ce.services.rule_execution_service import RuleExecutionService
from datamimic_ce.statements.mapping_statement import MappingStatement
from datamimic_ce.statements.rule_statement import RuleStatement
from datamimic_ce.tasks.base_constraint_task import BaseConstraintTask

logger = logging.getLogger("datamimic")


class MappingTask(BaseConstraintTask):
    """
    Task that applies mapping rules to transform data.
    """

    def __init__(self, statement: MappingStatement):
        super().__init__(statement)

    @property
    def statement(self) -> MappingStatement:
        return self._statement  # type: ignore

    def _convert_numeric_strings(self, data_dict):
        """Helper function to convert string values to numeric types where appropriate."""
        for key, value in list(data_dict.items()):
            if isinstance(value, str):
                try:
                    # Try to convert to int first
                    if value.isdigit() or (value.startswith("-") and value[1:].isdigit()):
                        data_dict[key] = int(value)
                    # Then try float
                    else:
                        try:
                            float_val = float(value)
                            data_dict[key] = float_val
                        except ValueError:
                            pass  # Keep as string if conversion fails
                except Exception as e:
                    logger.debug(f"Error converting value for {key}: {e}")
        return data_dict

    def execute(
        self, source_data, pagination: DataSourcePagination | None = None, cyclic: bool | None = False
    ) -> list[Any] | GenIterContext:
        """
        Execute the mapping task.

        Args:
            source_data: The source data to be mapped
            pagination: Optional pagination configuration
            cyclic: Whether to cycle through the source data

        Returns:
            The mapped data or updated GenIterContext
        """
        # Handle GenIterContext case (integration with generate workflow)
        if isinstance(source_data, GenIterContext):
            return self._process_geniter_context(source_data)

        # Handle regular data flow for source data as a list
        mapping_data = list(source_data)
        # If source is empty, return empty list
        if len(mapping_data) == 0:
            return []

        for i, data_dict in enumerate(mapping_data):
            for key, value in data_dict.items():
                if isinstance(value, dict):
                    data_dict[key] = DotableDict(value)

            # Convert string values to numeric types where appropriate
            data_dict = self._convert_numeric_strings(data_dict)

            # Process each rule using the rule execution service
            for child_stmt in self.statement.sub_statements:
                if isinstance(child_stmt, RuleStatement):
                    # Use RuleExecutionService to evaluate and execute the rule
                    data_dict, _ = RuleExecutionService.execute_rule_for_dict(
                        rule_statement=child_stmt, data_dict=data_dict, rule_owner=self.__class__.__name__
                    )

            # Update the original data with the modified values
            for key, value in data_dict.items():
                if not key.startswith("_"):
                    mapping_data[i][key] = value

        # Apply pagination and return the result
        return self._apply_pagination(mapping_data, pagination, cyclic or False)
