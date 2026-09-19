# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import sys

from datamimic_ce.contexts.context import Context
from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination
from datamimic_ce.domains.domain_core.base_literal_generator import BaseLiteralGenerator
from datamimic_ce.statements.key_statement import KeyStatement
from datamimic_ce.statements.variable_statement import VariableStatement


class SequenceTableGenerator(BaseLiteralGenerator):
    """
    Generate sequential number set based on database sequence.

    This generator manages sequence numbers for database tables, handling pagination
    and sequential number generation. It works with both KeyStatement and VariableStatement
    types and is compatible with SQLAlchemy 2.x. Each process reserves its own range via
    context.root.process_id (wired in generate_worker.py's mp_preprocess - previously dead:
    every worker read it as None/0, making the per-process offset a no-op; fixed and verified
    under an uneven count/numProcess ratio, see tests_ce/external_service_tests/
    test_sequence_table_generator/test_sequence_table_generator_postgres_uneven_multiprocess).

    Multiprocess safety here is client-side range math (each worker computes its own offset,
    not a server-side atomic block reservation): DATAMIMIC EE's equivalent generator instead
    declares itself __parallel_safe__ = False outright ("reserves DB sequence ranges per
    process") rather than relying on this pattern for ANY dialect - i.e. EE's own engineering
    judgment is that per-process client-side range math isn't worth trusting for its multiprocess
    guarantees. CE's per-dialect reality, verified empirically this session, does NOT uniformly
    match that pessimism:

    - Postgres: rdbms_client.get_current_sequence_number/increase_sequence_number use the
      dialect's own nextval/setval, single atomic server-side statements with no client-side
      read-then-write round trip - genuinely safe under concurrent workers (confirmed 8/8
      consecutive real-multiprocess runs of the uneven count/numProcess regression test, see
      test_sequence_table_generator_postgres_uneven_multiprocess).
    - MySQL: has no native sequence object, so increase_sequence_number emulates one via a
      GET_LOCK-guarded read-AUTO_INCREMENT-then-ALTER-TABLE critical section
      (_advance_mysql_auto_increment). This is exactly the class of client-side range math EE
      opted out of, and it shows: reproduced as real duplicate-key collisions in ~2/3 of
      isolated real-multiprocess runs of the uneven-ratio case (the regression now asserts that
      test_sequence_table_generator_mysql_uneven_multiprocess is rejected before execution). MySQL
      sequence generation is rejected when numProcess is greater than one in CE, matching EE's
      judgment for this dialect.
    - MSSQL/Oracle: native-sequence support was prototyped and pulled (see
      get_current_sequence_number's docstring) - unsupported regardless of process count.

    This fix (wiring context.root.process_id, previously dead) closes a definite bug either way -
    before it, EVERY dialect's per-process offset was a no-op, so even Postgres's provably-atomic
    nextval/setval couldn't have kept workers' ranges apart. The fix just doesn't retroactively
    make MySQL's weaker mechanism trustworthy under real concurrency.

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
        sequence: str | None = None,
    ):
        """
        Initialize the sequence table generator.

        Args:
            context: Context object containing configuration and state
            stmt: Statement object containing sequence configuration
            sequence: Optional explicit DB sequence name (e.g. 'zsv.t_angebote_id_seq' for a
                schema-qualified native sequence, as migrated legacy descriptors name them). When
                None, falls back to the convention-derived f"{type}_{name}_seq". Caution: a
                sequence that doesn't exist is still auto-created starting at 1, so a typo'd
                explicit name silently mints a fresh sequence instead of erroring - against a
                live table with real rows that means duplicate keys.

        Raises:
            ValueError: If required attributes are missing or invalid
            AttributeError: If database client is not properly configured
        """
        self._stmt = stmt
        self._context = context
        self._process_id: int | None = None
        self._current: int | None = None
        self._end: int | None = None
        self._explicit_sequence_name = sequence or None  # "" falls back to convention too

        # Handle database attribute access safely
        if not hasattr(stmt, "database"):
            raise ValueError(f"Statement type {type(stmt).__name__} must have 'database' attribute")
        self._source_name = stmt.database

        rdbms_client = context.root.clients.get(self._source_name)
        if rdbms_client is None:
            raise ValueError(f"No database client found for source: {self._source_name}")

        # Get root generate statement safely (stashed: the root of a key/variable cannot change
        # over this instance's lifetime, so pre_execute reuses it instead of re-walking the tree)
        root_gen_stmt = self._stmt.get_root_generate_statement()
        if root_gen_stmt is None:
            raise ValueError("Root generate statement is required")
        self._root_gen_stmt = root_gen_stmt

        # Initialize sequence with process-safe range
        try:
            total_processes = self._root_gen_stmt.num_process or context.root.num_process or 1
            credential = getattr(rdbms_client, "credential", None)
            if total_processes > 1 and getattr(credential, "dbms", None) == "mysql":
                raise ValueError(
                    "SequenceTableGenerator with a MySQL source is single-process only; "
                    "set numProcess=1 because MySQL has no atomic native sequence reservation"
                )
            self._process_id = context.root.process_id or 0

            total_count = int(root_gen_stmt.count)

            # Calculate per-process count
            per_process_count = (total_count + total_processes - 1) // total_processes
            # Every worker is allocated a UNIFORM per_process_count-sized slice (process_offset
            # below), even when total_count doesn't divide evenly - e.g. count=13, numProcess=4
            # gives per_process_count=4, i.e. a reserved block of 4*4=16, 3 more than the 13
            # actually needed. pre_execute() must reserve that same rounded-up block (not raw
            # total_count), or the last worker's assumed range overlaps the next run's - this
            # wastes a few sequence values on the excess but keeps the per-process arithmetic
            # simple and collision-free, rather than special-casing the uneven last chunk.
            reserved_count = per_process_count * total_processes

            # Get current sequence and calculate process-specific range
            current_seq = rdbms_client.get_current_sequence_number(
                sequence_name=self._resolve_sequence_name(),
                table_name=None if self._explicit_sequence_name else self._root_gen_stmt.type,
                column_name=None if self._explicit_sequence_name else self._stmt.name,
            )

            # Calculate process-specific offset to avoid conflicts
            process_offset = self._process_id * per_process_count
            self._start = current_seq - reserved_count + process_offset

            # Store process information for later use
            self._total_processes = total_processes
            self._per_process_count = per_process_count

        except Exception as e:
            raise ValueError(f"Failed to initialize sequence: {str(e)}") from e

    def _resolve_sequence_name(self) -> str:
        """Explicit sequence= name if given (e.g. a migrated legacy descriptor's DB sequence name,
        schema-qualified or not); otherwise the existing convention f"{type}_{name}_seq"."""
        if self._explicit_sequence_name:
            return self._explicit_sequence_name
        return f"{self._root_gen_stmt.type}_{self._stmt.name}_seq"

    def pre_execute(self, context: Context) -> None:
        """
        Increase the sequence number in the database before execution.
        Each process will update its own range of sequence numbers.

        Args:
            context: Context object containing configuration and state

        Raises:
            ValueError: If required statements or attributes are missing
        """
        rdbms_client = context.root.clients.get(self._source_name)
        if rdbms_client is None:
            raise ValueError(f"No database client found for source: {self._source_name}")

        # Reserve the SAME rounded-up block __init__ assumed (per_process_count * total_processes,
        # not the raw statement count) - keeps this in sync with the per-process offset arithmetic
        # above for an uneven count/numProcess ratio (see the comment in __init__).
        rdbms_client.increase_sequence_number(
            sequence_name=self._resolve_sequence_name(),
            increment=self._per_process_count * self._total_processes,
            table_name=None if self._explicit_sequence_name else self._root_gen_stmt.type,
            column_name=None if self._explicit_sequence_name else self._stmt.name,
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
