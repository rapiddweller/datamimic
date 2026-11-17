# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import sys

from datamimic_ce.domains.api import BaseLiteralGenerator
from datamimic_ce.engine.dsl.api import KeyStatement, VariableStatement, get_nearest_generate_statement
from datamimic_ce.engine.io.api import (
    DataSourcePagination,
    rdbms_get_current_sequence_number,
    rdbms_increase_sequence_number,
    uses_mysql_sequence_storage,
)
from datamimic_ce.engine.runtime.contexts.context import Context
from datamimic_ce.errors import DomainError, UserErrorBase, generator_config_error


class SequenceTableGenerator(BaseLiteralGenerator):
    """
    Generate sequential number set based on database sequence.

    This generator manages sequence numbers for database tables, handling pagination
    and sequential number generation for key statements. It is compatible with SQLAlchemy 2.x.
    One block of per_process_count * numProcess numbers is reserved; a page's rows are the
    block offsets [skip, skip + limit), where skip is the global row index of the page, so
    every worker's chunk maps onto its own slice of the block.

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

    Attributes:
        _stmt: The statement (KeyStatement or VariableStatement) containing sequence configuration
        _source_name: Name of the database source
        _start: First number of the reserved block (immutable; pages are offsets from it)
        _current: Current sequence number
        _end: End sequence number (used for pagination)
        _page: (skip, limit) of the page the generator is currently positioned on
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
        self._page: tuple[int, int] | None = None
        self._current: int | None = None
        self._end: int | None = None
        self._explicit_sequence_name = sequence or None  # "" falls back to convention too

        if isinstance(stmt, VariableStatement):
            raise generator_config_error(reason="SequenceTableGenerator requires a key with a database attribute")
        source_name = stmt.database
        if source_name is None:
            raise generator_config_error(reason="SequenceTableGenerator requires a configured database client")
        self._source_name: str = source_name

        rdbms_client = context.root.clients.get(self._source_name)
        if rdbms_client is None:
            raise generator_config_error(reason="SequenceTableGenerator requires a configured database client")

        # Get root generate statement safely (stashed: the root of a key/variable cannot change
        # over this instance's lifetime, so pre_execute reuses it instead of re-walking the tree)
        root_gen_stmt = get_nearest_generate_statement(self._stmt)
        if root_gen_stmt is None:
            raise generator_config_error(reason="Root generate statement is required")
        self._root_gen_stmt = root_gen_stmt

        # Initialize sequence with process-safe range
        try:
            total_processes = self._root_gen_stmt.num_process or context.root.num_process or 1
            uses_mysql = uses_mysql_sequence_storage(rdbms_client)
            if total_processes > 1 and uses_mysql:
                raise generator_config_error(
                    reason=(
                        "SequenceTableGenerator with a MySQL source is single-process only; "
                        "set numProcess=1 because MySQL has no atomic native sequence reservation"
                    )
                )
            count = root_gen_stmt.count
            if count is None:
                raise generator_config_error(reason="SequenceTableGenerator requires a generate count")
            total_count = int(count)

            # Calculate per-process count
            per_process_count = (total_count + total_processes - 1) // total_processes
            # Every worker is allocated a UNIFORM per_process_count-sized slice (chunk skip
            # below), even when total_count doesn't divide evenly - e.g. count=13, numProcess=4
            # gives per_process_count=4, i.e. a reserved block of 4*4=16, 3 more than the 13
            # actually needed. pre_execute() must reserve that same rounded-up block (not raw
            # total_count), or the last worker's assumed range overlaps the next run's - this
            # wastes a few sequence values on the excess but keeps the per-process arithmetic
            # simple and collision-free, rather than special-casing the uneven last chunk.
            reserved_count = per_process_count * total_processes

            # Get current sequence and calculate process-specific range
            current_seq = rdbms_get_current_sequence_number(
                rdbms_client,
                self._resolve_sequence_name(),
                None if self._explicit_sequence_name else self._root_gen_stmt.type,
                None if self._explicit_sequence_name else self._stmt.name,
            )

            # Pagination skips are global row indices (chunk starts already encode the worker's
            # slice), so the block start carries no per-process offset.
            self._start = current_seq - reserved_count

            self._total_processes = total_processes
            self._per_process_count = per_process_count

        except (UserErrorBase, DomainError):
            raise
        except Exception as e:
            raise generator_config_error(
                reason=f"SequenceTableGenerator initialization failed ({type(e).__name__})"
            ) from e

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
            raise generator_config_error(reason="SequenceTableGenerator requires a configured database client")

        # Reserve the SAME rounded-up block __init__ assumed (per_process_count * total_processes,
        # not the raw statement count) - keeps this in sync with the per-process offset arithmetic
        # above for an uneven count/numProcess ratio (see the comment in __init__).
        reserved_count = self._per_process_count * self._total_processes
        rdbms_increase_sequence_number(
            rdbms_client,
            self._resolve_sequence_name(),
            reserved_count,
            None if self._explicit_sequence_name else self._root_gen_stmt.type,
            None if self._explicit_sequence_name else self._stmt.name,
        )
        # The block just reserved is the one ending at the next number: re-anchor on it so every
        # worker inheriting this instance shares one block start (each read advances the sequence).
        self._start = (
            rdbms_get_current_sequence_number(
                rdbms_client,
                self._resolve_sequence_name(),
                None if self._explicit_sequence_name else self._root_gen_stmt.type,
                None if self._explicit_sequence_name else self._stmt.name,
            )
            - reserved_count
        )
        # A new block invalidates the positioned page: the next add_pagination re-positions on it.
        self._page = None

    def add_pagination(self, pagination: DataSourcePagination | None = None) -> None:
        """
        Position the generator on a page: rows [skip, skip + limit) of the reserved block.

        Derived from the immutable block start, so applying a new page to a cached instance
        replaces the previous page; re-applying the page already in use keeps the position.

        Args:
            pagination: Optional pagination configuration
        """
        if pagination is None:
            self._page = None
            self._end = sys.maxsize
            self._current = self._start + 1
            return

        page = (pagination.skip, pagination.limit)
        if page == self._page:
            return
        self._page = page
        self._current = self._start + pagination.skip
        self._end = self._current + pagination.limit

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
