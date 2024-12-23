# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import sys

from datamimic_ce.contexts.context import Context
from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination
from datamimic_ce.generators.generator import Generator
from datamimic_ce.statements.key_statement import KeyStatement
from datamimic_ce.statements.variable_statement import VariableStatement


class SequenceTableGenerator(Generator):
    """
    Generate sequential number set based on database sequence.

    This generator manages sequence numbers for database tables, handling pagination
    and sequential number generation. It works with both KeyStatement and VariableStatement
    types and is compatible with SQLAlchemy 2.x. The generator ensures thread and process
    safety by reserving unique ranges for each process.

    Attributes:
        _stmt: The statement (KeyStatement or VariableStatement) containing sequence configuration
        _context: The context object containing configuration and state
        _source_name: Name of the database source
        _start: Starting sequence number for this generator instance
        _current: Current sequence number
        _end: End sequence number (used for pagination)
        _process_id: Current process ID for multi-process safety
    """

    def __init__(
        self,
        context: Context,
        stmt: KeyStatement | VariableStatement,
    ):
        """
        Initialize the sequence table generator.

        Args:
            context: Context object containing configuration and state
            stmt: Statement object containing sequence configuration

        Raises:
            ValueError: If required attributes are missing or invalid
            AttributeError: If database client is not properly configured
        """
        self._stmt = stmt
        self._context = context
        self._process_id: int | None = None
        self._current: int | None = None
        self._end: int | None = None

        # Handle database attribute access safely
        if not hasattr(stmt, "database"):
            raise ValueError(f"Statement type {type(stmt).__name__} must have 'database' attribute")
        self._source_name = stmt.database

        # Get database client safely
        if not hasattr(context.root, "clients"):
            raise AttributeError("Context root must have 'clients' attribute")
        rdbms_client = context.root.clients.get(self._source_name)
        if rdbms_client is None:
            raise ValueError(f"No database client found for source: {self._source_name}")

        # Get root generate statement safely
        root_gen_stmt = self._stmt.get_root_generate_statement()
        if root_gen_stmt is None:
            raise ValueError("Root generate statement is required")

        # Initialize sequence with process-safe range
        try:
            # Get process information from context
            total_processes = context.root.num_process or 1 if hasattr(context.root, "num_process") else 1

            if hasattr(context.root, "process_id"):
                self._process_id = context.root.process_id
            else:
                self._process_id = 0

            total_count = int(root_gen_stmt.count)

            # Calculate per-process count
            per_process_count = (total_count + total_processes - 1) // total_processes

            # Get current sequence and calculate process-specific range
            current_seq = rdbms_client.get_current_sequence_number(
                sequence_name=f"{root_gen_stmt.type}_{self._stmt.name}_seq"
            )

            # Calculate process-specific offset to avoid conflicts
            process_offset = self._process_id * per_process_count
            self._start = current_seq - total_count + process_offset

            # Store process information for later use
            self._total_processes = total_processes
            self._per_process_count = per_process_count

        except Exception as e:
            raise ValueError(f"Failed to initialize sequence: {str(e)}") from e

    def pre_execute(self, context: Context) -> None:
        """
        Increase the sequence number in the database before execution.
        Each process will update its own range of sequence numbers.

        Args:
            context: Context object containing configuration and state

        Raises:
            ValueError: If required statements or attributes are missing
        """
        root_gen_stmt = self._stmt.get_root_generate_statement()
        if root_gen_stmt is None:
            raise ValueError("Root generate statement is required for pre_execute")

        rdbms_client = context.root.clients.get(self._source_name)
        if rdbms_client is None:
            raise ValueError(f"No database client found for source: {self._source_name}")

        rdbms_client.increase_sequence_number(
            sequence_name=f"{root_gen_stmt.type}_{self._stmt.name}_seq", increment=root_gen_stmt.count
        )

    def add_pagination(self, pagination: DataSourcePagination | None = None) -> None:
        """
        Add pagination to the generator.

        Args:
            pagination: Optional pagination configuration
        """
        if pagination is None:
            self._end = sys.maxsize
            self._current = self._start + 1
            return

        # Calculate process-specific pagination
        if self._process_id is not None and self._total_processes > 1:
            # Adjust skip based on process ID
            process_skip = pagination.skip + (self._process_id * self._per_process_count)
            # Ensure limit doesn't exceed per-process count
            process_limit = min(pagination.limit, self._per_process_count)

            self._start = self._start + process_skip
            self._end = self._start + process_limit
        else:
            # Single process mode
            self._start = self._start + pagination.skip
            self._end = self._start + pagination.limit

        self._current = self._start

    def generate(self) -> int:
        """
        Generate current number of sequence.

        Returns:
            int: The next sequence number

        Raises:
            StopIteration: When sequence generation is complete or invalid
        """
        if self._current is None:
            raise StopIteration("Generator cannot generate value: sequence not initialized")
        if self._end is None:
            raise StopIteration("Generator cannot generate value: end sequence not set")

        result = self._current
        self._current += 1

        if self._current > self._end:
            raise StopIteration("Generator reached the end of sequence")

        return result
