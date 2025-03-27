# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
import logging
from typing import Any

from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination
from datamimic_ce.statements.target_constraints_statement import TargetConstraintsStatement
from datamimic_ce.tasks.base_constraint_task import BaseConstraintTask

logger = logging.getLogger("datamimic")


class TargetConstraintsTask(BaseConstraintTask):
    """
    Task that applies target constraints to filter and transform data after mapping.
    """

    def __init__(self, statement: TargetConstraintsStatement):
        super().__init__(statement)

    @property
    def statement(self) -> TargetConstraintsStatement:
        return self._statement  # type: ignore

    def execute(
        self, source_data, pagination: DataSourcePagination | None = None, cyclic: bool | None = False
    ) -> list[Any] | GenIterContext:
        """
        Execute the target constraints task.

        Args:
            source_data: The source data to be filtered/transformed
            pagination: Optional pagination configuration
            cyclic: Whether to cycle through the source data

        Returns:
            The filtered/transformed data or updated GenIterContext
        """
        # Use standard execution flow with filtering mode
        return self._handle_standard_execution(
            source_data=source_data, pagination=pagination, cyclic=cyclic, filter_mode=True
        )
