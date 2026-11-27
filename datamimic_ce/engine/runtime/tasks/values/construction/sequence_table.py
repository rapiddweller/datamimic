# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.domains.api import BaseLiteralGenerator
from datamimic_ce.engine.dsl.api import (
    KeyStatement,
    NestedKeyStatement,
    Statement,
    VariableStatement,
    get_nearest_generate_statement,
)
from datamimic_ce.engine.io.api import (
    Client,
    DataSourcePagination,
    rdbms_reserve_sequence_block,
    uses_mysql_sequence_storage,
)
from datamimic_ce.engine.runtime.contexts.context import Context
from datamimic_ce.errors import DomainError, UserErrorBase, generator_config_error


class SequenceTableGenerator(BaseLiteralGenerator):
    """Generate increasing integers from blocks allocated to cooperating DATAMIMIC runs.

    PostgreSQL uses an ascending, unit-increment sequence; MySQL uses the target table's
    AUTO_INCREMENT counter and runs with one worker. Other dialects are unsupported.
    Clients that bypass DATAMIMIC's reservation lock are outside the collision guarantee.
    Separate runs may leave gaps, for example if a run fails after reserving its block.

    Direct generate keys reserve before workers start. Each page uses its global offset
    in the shared block of planned rows. Keys created only at execution time reserve
    their own block for each invocation of the enclosing generate.
    """

    def __init__(
        self,
        context: Context,
        stmt: KeyStatement | VariableStatement,
        sequence: str | None = None,
        pagination: DataSourcePagination | None = None,
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
            pagination: The page, or the complete local window for a nestedKey child.

        Raises:
            ValueError: If required attributes are missing or invalid
            AttributeError: If database client is not properly configured
        """
        self._stmt = stmt
        self._start: int | None = None
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
        if not isinstance(rdbms_client, Client):
            raise generator_config_error(reason="SequenceTableGenerator requires a configured database client")
        self._initial_client: Client | None = rdbms_client

        # Get root generate statement safely (stashed: the root of a key/variable cannot change
        # over this instance's lifetime, so pre_execute reuses it instead of re-walking the tree)
        root_gen_stmt = get_nearest_generate_statement(self._stmt)
        if root_gen_stmt is None:
            raise generator_config_error(reason="Root generate statement is required")
        self._root_gen_stmt = root_gen_stmt
        self._generation_plan = root_gen_stmt.generation_plan
        self._nested_window = pagination if isinstance(stmt.parent_stmt, NestedKeyStatement) else None

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
            if self._nested_window is not None:
                total_count = self._nested_window.limit
                total_processes = 1
            elif self._generation_plan is not None:
                _, total_count = self._generation_plan
            else:
                count = root_gen_stmt.count
                if count is None:
                    raise generator_config_error(reason="SequenceTableGenerator requires a generate count")
                total_count = int(count)

            # Match the worker planner's uniform slices, including any unused part of the last one.
            per_process_count = (total_count + total_processes - 1) // total_processes
            self._reserved_count = per_process_count * total_processes

        except (UserErrorBase, DomainError):
            raise
        except Exception as e:
            raise generator_config_error(
                reason=f"SequenceTableGenerator initialization failed ({type(e).__name__})"
            ) from e

    def matches_invocation(self, stmt: Statement, pagination: DataSourcePagination | None) -> bool:
        # NestedKeyTask creates a fresh, unshared pagination object for each local window.
        if isinstance(stmt.parent_stmt, NestedKeyStatement) and self._nested_window is not pagination:
            return False
        generate = get_nearest_generate_statement(stmt)
        return generate is not None and generate.generation_plan == self._generation_plan

    def _resolve_sequence_name(self) -> str:
        """Explicit sequence= name if given (e.g. a migrated legacy descriptor's DB sequence name,
        schema-qualified or not); otherwise the existing convention f"{type}_{name}_seq"."""
        if self._explicit_sequence_name:
            return self._explicit_sequence_name
        return f"{self._root_gen_stmt.type}_{self._stmt.name}_seq"

    def pre_execute(self, context: Context) -> None:
        """Reserve a fresh block for this invocation, before worker context serialization."""
        rdbms_client = context.root.clients.get(self._source_name)
        if not isinstance(rdbms_client, Client):
            raise generator_config_error(reason="SequenceTableGenerator requires a configured database client")
        self._reserve(rdbms_client)
        self._page = None
        self._current = None
        self._end = None

    def _reserve(self, client: Client) -> None:
        self._start = (
            rdbms_reserve_sequence_block(
                client,
                self._resolve_sequence_name(),
                self._reserved_count,
                None if self._explicit_sequence_name else self._root_gen_stmt.type,
                None if self._explicit_sequence_name else self._stmt.name,
            )
            if self._reserved_count
            else 0
        )
        # A prepared worker needs only the block and offsets, not another client connection.
        self._initial_client = None

    def add_pagination(self, pagination: DataSourcePagination | None = None) -> None:
        """Position on a page within the block. Reapplying the same page keeps the cursor."""
        if self._initial_client is not None:
            self._reserve(self._initial_client)
        assert self._start is not None
        page = (pagination.skip, pagination.limit) if pagination else (0, self._reserved_count)
        if page == self._page:
            return
        self._page = page
        skip, limit = page
        self._current = self._start + max(0, skip)
        self._end = min(self._current + limit, self._start + self._reserved_count)

    def generate(self) -> int:
        if self._page is None:
            self.add_pagination()
        assert self._current is not None and self._end is not None
        if self._current >= self._end:
            raise StopIteration("Generator reached the end of sequence")
        result = self._current
        self._current += 1
        return result
