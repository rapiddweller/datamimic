# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
import copy
import itertools
import logging
from typing import Any, TypeVar

from datamimic_ce.contexts.context import DotableDict
from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination
from datamimic_ce.services.rule_execution_service import RuleExecutionService
from datamimic_ce.statements.composite_statement import CompositeStatement
from datamimic_ce.statements.rule_statement import RuleStatement

logger = logging.getLogger("datamimic")

T = TypeVar("T")


class DataTransformationService:
    """
    Service for handling common data transformation operations across different task types.

    This centralizes various data handling patterns that were previously duplicated:
    - Dictionary type conversions
    - GenIterContext handling
    - Pagination and data slicing
    - Deep copy operations
    - Dictionary transformation to DotableDict
    """

    @staticmethod
    def convert_numeric_strings(data_dict: dict[str, Any]) -> dict[str, Any]:
        """
        Convert string values to appropriate numeric types where possible.

        Args:
            data_dict: Dictionary containing values to be converted

        Returns:
            Dictionary with string values converted to appropriate numeric types
        """
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

    @staticmethod
    def convert_dict_to_dotable(data_dict: dict[str, Any]) -> dict[str, Any]:
        """
        Convert nested dictionaries to DotableDict for easier access.

        Args:
            data_dict: Dictionary to process

        Returns:
            Dictionary with nested dictionaries converted to DotableDict
        """
        for key, value in data_dict.items():
            if isinstance(value, dict):
                data_dict[key] = DotableDict(value)
        return data_dict

    @staticmethod
    def process_data_with_rules(
        data_list: list[dict[str, Any]], statement: CompositeStatement, rule_owner: str, filter_mode: bool = True
    ) -> list[dict[str, Any]]:
        """
        Process a list of dictionaries by applying rules from a composite statement.

        Args:
            data_list: List of dictionaries to process
            statement: Composite statement containing rules to apply
            rule_owner: Name of the component executing the rules (for logging)
            filter_mode: Whether to filter out items that don't meet rules (True) or just transform them (False)

        Returns:
            Processed list of dictionaries
        """
        result_data = list(data_list)

        if len(result_data) == 0:
            return []

        # When in filter mode, process in reverse order to safely remove items
        indices = range(len(result_data) - 1, -1, -1) if filter_mode else range(len(result_data))

        for i in indices:
            # Deep copy to avoid modifying original data during processing
            data_dict = copy.deepcopy(result_data[i])

            # Convert nested dictionaries to DotableDict
            data_dict = DataTransformationService.convert_dict_to_dotable(data_dict)

            # Convert string values to numeric types where appropriate
            data_dict = DataTransformationService.convert_numeric_strings(data_dict)

            should_filter = False

            # Process each rule
            for child_stmt in statement.sub_statements:
                if isinstance(child_stmt, RuleStatement):
                    data_dict, should_filter_record = RuleExecutionService.execute_rule_for_dict(
                        rule_statement=child_stmt, data_dict=data_dict, rule_owner=rule_owner
                    )

                    if should_filter_record and filter_mode:
                        should_filter = True
                        break

            if should_filter and filter_mode:
                del result_data[i]  # Remove data that doesn't meet rules
            else:
                # Update original data with modified values
                for key, value in data_dict.items():
                    if not key.startswith("_"):  # Skip internal variables
                        result_data[i][key] = value

        return result_data

    @staticmethod
    def apply_pagination(data_list: list[Any], pagination: DataSourcePagination | None, cyclic: bool) -> list[Any]:
        """
        Apply pagination and cyclic behavior to data.

        Args:
            data_list: List of data items to paginate
            pagination: Optional pagination configuration
            cyclic: Whether to cycle through the data

        Returns:
            Paginated (and possibly cycled) data
        """
        # If data is empty, return empty list
        if len(data_list) == 0:
            return []

        # Determine start and end indices based on pagination
        if pagination is None:
            start_idx = 0
            end_idx = len(data_list)
        else:
            start_idx = pagination.skip
            end_idx = pagination.skip + pagination.limit

        # Apply cyclic behavior if requested
        if cyclic:
            iterator = itertools.cycle(data_list)
            return [copy.deepcopy(ele) for ele in itertools.islice(iterator, start_idx, end_idx)]
        else:
            return list(itertools.islice(data_list, start_idx, end_idx))
