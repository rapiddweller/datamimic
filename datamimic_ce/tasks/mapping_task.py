# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
import logging
from typing import Any

from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination
from datamimic_ce.statements.mapping_statement import MappingStatement
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
        # Use standard execution flow without filtering mode
        return self._handle_standard_execution(
            source_data=source_data, pagination=pagination, cyclic=cyclic, filter_mode=False
        )
