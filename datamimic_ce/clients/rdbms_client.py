# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import re
import sys
from pathlib import Path
from typing import Any, cast
from urllib.parse import quote

import oracledb
import sqlalchemy
from sqlalchemy import MetaData, func, inspect, select, text
from sqlalchemy.engine import Dialect
from sqlalchemy.pool import QueuePool

from datamimic_ce.clients.database_client import DatabaseClient
from datamimic_ce.config import settings
from datamimic_ce.connection_config.rdbms_connection_config import RdbmsConnectionConfig
from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination
from datamimic_ce.domains.domain_core.base_entity import stringify_if_entity
from datamimic_ce.logger import logger

# SQLAlchemy create_engine kwargs DATAMIMIC forwards (pooling/behavior). Anything else in the
# connection config is either connection identity (see _CONNECTION_IDENTITY, used to build the URL)
# or a vendor knob that create_engine would reject.
_ENGINE_KWARGS = {
    "echo",
    "echo_pool",
    "pool_size",
    "max_overflow",
    "pool_timeout",
    "pool_recycle",
    "pool_pre_ping",
    "connect_args",
    "isolation_level",
    "execution_options",
    "encoding",
    "future",
}
# Connection identity used to build the URL (not passed as an engine kwarg) - dropping these is expected.
_CONNECTION_IDENTITY = {
    "dbms",
    "database",
    "host",
    "port",
    "user",
    "password",
    "db_schema",
    "id",
    "environment",
    "system",
    "none_as_null_col",
}


class RdbmsClient(DatabaseClient):
    def __init__(self, credential: RdbmsConnectionConfig, task_id: str | None = None):
        self._credential = credential
        self._engine = None
        self._task_id = task_id

        # Keep only real SQLAlchemy create_engine kwargs. The connection config allows extra keys
        # (env files carry connection identity like dbms/host plus vendor knobs such as legacy
        # clean/catalog/quoteTableNames); anything not a create_engine parameter would raise, so allowlist.
        all_config = credential.get_connection_config()
        self._engine_kwargs = {k: v for k, v in all_config.items() if k in _ENGINE_KWARGS}
        dropped = set(all_config) - set(self._engine_kwargs) - _CONNECTION_IDENTITY
        if dropped:
            logger.debug(f"Ignored non-engine connection keys: {', '.join(sorted(dropped))}")
        # Set default values for some kwargs
        self._engine_kwargs["echo"] = self._engine_kwargs.get("echo", False)
        self._engine_kwargs["pool_size"] = self._engine_kwargs.get("pool_size", 20)
        self._engine_kwargs["max_overflow"] = self._engine_kwargs.get("max_overflow", 30)
        self._engine_kwargs["pool_timeout"] = self._engine_kwargs.get("pool_timeout", 30)
        self._engine_kwargs["pool_pre_ping"] = self._engine_kwargs.get("pool_pre_ping", True)

    @property
    def engine(self):
        return self._engine

    @engine.setter
    def engine(self, value):
        self._engine = value

    def _create_engine(self):
        """
        Create SQLAlchemy engine based on provided credentials and database management system (DBMS).
        :return: SQLAlchemy engine instance
        """
        # Return the existing engine if it has already been created
        if self._engine is not None:
            return self._engine

        # Extract database credentials and parameters
        dbms = self._credential.dbms
        db = self._credential.database
        user = None if self._credential.user is None else quote(self._credential.user)
        password = None if self._credential.password is None else quote(self._credential.password)
        host = self._credential.host
        port = self._credential.port

        def create_sqlite_engine(file_path):
            """
            Create an SQLite engine.
            :param file_path: Path to the SQLite database file
            :return: SQLAlchemy engine for SQLite
            """
            logger.info(f"Using SQLite database at {file_path}")
            return sqlalchemy.create_engine(f"sqlite:///{file_path}", **self._engine_kwargs)

        def create_sqlalchemy_engine(driver, user, password, host, port, db):
            """
            Create a generic SQLAlchemy engine.
            :param driver: The database driver
            :param user: Database user
            :param password: Database password
            :param host: Database host
            :param port: Database port
            :param db: Database name
            :return: SQLAlchemy engine
            """
            return sqlalchemy.create_engine(
                f"{driver}://{user}:{password}@{host}:{port}/{db}",
                poolclass=QueuePool,
                **self._engine_kwargs,
            )

        # Match the DBMS type and create the appropriate SQLAlchemy engine
        match dbms:
            case "sqlite":
                environment = settings.RUNTIME_ENVIRONMENT
                if environment in {"development", "production"}:
                    if not self._task_id:
                        raise ValueError("Task ID is required to create SQLite db in task folder")
                    # Construct the database path within the task folder
                    db_path = Path("db") / f"{db}.sqlite"
                    if not db_path.exists():
                        # Ensure the parent directory exists
                        logger.info(f"Creating SQLite db file in task folder: {db_path}")
                        db_path.parent.mkdir(parents=True, exist_ok=True)

                else:
                    # Use a simple file-based SQLite database
                    db_path = Path(f"{db}.sqlite")
                self._engine = create_sqlite_engine(db_path)

            case "mssql":
                # ODBC Driver 17 (pyodbc) is the default; opt into the pure-Python pymssql/FreeTDS
                # driver with driver="pymssql" on the <database> credential - no proprietary MS
                # ODBC package to install, avoids the exact driver-install friction that pushed
                # DATAMIMIC EE to make pymssql its own default (rdbms/url_builder.py).
                if getattr(self._credential, "driver", None) == "pymssql":
                    self._engine = create_sqlalchemy_engine("mssql+pymssql", user, password, host, port, db)
                else:
                    self._engine = create_sqlalchemy_engine(
                        "mssql+pyodbc",
                        user,
                        password,
                        host,
                        port,
                        f"{db}?driver=ODBC+Driver+17+for+SQL+Server",
                    )

            case "oracle":
                # Set OracleDB version and import the necessary module
                oracledb.version = "8.3.0"
                sys.modules["cx_Oracle"] = oracledb
                self._engine = create_sqlalchemy_engine("oracle", user, password, host, port, f"?service_name={db}")

            case _:
                # For other DBMS types, use a generic method to get the driver and create the engine
                driver = RdbmsClient._get_driver_for_dbms(dbms)
                self._engine = create_sqlalchemy_engine(driver, user, password, host, port, db)

        return self._engine

    def _get_metadata(self, engine):
        """
        Get metadata of database
        :param engine:
        :return:
        """
        metadata = MetaData()
        # Reflect the table schema from the database
        metadata.reflect(bind=engine, schema=self._credential.db_schema)

        return metadata

    def _apply_global_json_config(self, data_list: list[dict]) -> list[dict]:
        """
        Apply global JSON configuration to the given data list.
        If the 'none_as_null_col' configuration from the credential is enabled,
        converts any None value to a SQLAlchemy NULL value.

        :param data_list: List of dictionaries representing rows to be processed.
        :return: The transformed data list.
        """
        # Get the list of columns where None values should be converted to NULL.
        # Filter empties: "".split(",") is [""] and would inject a bogus ''-keyed column into every row.
        none_as_null_col = [
            col.strip() for col in getattr(self._credential, "none_as_null_col", "").split(",") if col.strip()
        ]
        # Convert None values to SQLAlchemy NULL
        if len(none_as_null_col) > 0:
            for idx, data_dict in enumerate(data_list):
                for col in none_as_null_col:
                    if data_dict.get(col) is None:
                        data_list[idx][col] = sqlalchemy.null()
        return data_list

    def get(self, query: str) -> list:
        """
        Get rows from database table
        :param query:
        :return:
        """
        # Establish a database connection
        with self._create_engine().connect() as connection:
            executable_query = sqlalchemy.text(query)
            result = connection.execute(executable_query)
            # Fetch all rows
            rows = result.fetchall()

        return rows

    def execute_sql_script(self, query: str) -> None:
        """
        Execute a SQL query without returning any result
        :param query:
        :return:
        """
        if query is None:
            return
        with self._create_engine().connect() as connection:
            transaction = connection.begin()
            try:
                # Split the SQL commands into individual commands since SQLite can execute sql statements one by one
                if self._credential.dbms in ("sqlite", "mysql"):
                    commands = query.split(";")
                    for command in commands:
                        if command.strip():
                            executable_query = sqlalchemy.text(command)
                            connection.execute(executable_query)
                elif self._credential.dbms == "oracle":
                    script = re.sub(r"--.*", "", query)  # Remove comments
                    edited_query_list = []  # keep query order
                    while script:
                        script = script.strip()
                        # check PL/SQL block index vs statement index
                        matches = re.search(r"(DECLARE|BEGIN|;)", script.upper())
                        if matches is not None:
                            matched_string = matches.group()
                            if matched_string in ("DECLARE", "BEGIN"):
                                # split PL/SQL block
                                blocks = script.split("END;", 1)
                                edited_query_list.append(f"{blocks[0]}END;")
                                script = blocks[1] if len(blocks) >= 2 else ""
                            else:
                                # split statement
                                blocks = script.split(";", 1)
                                edited_query_list.append(f"{blocks[0]}")
                                script = blocks[1] if len(blocks) >= 2 else ""
                        else:
                            break
                    for command in edited_query_list:
                        if command.strip():
                            executable_query = sqlalchemy.text(command)
                            connection.execute(executable_query)
                else:
                    executable_query = sqlalchemy.text(query)
                    connection.execute(executable_query)
                # Commit the changes to the database
                transaction.commit()
            except Exception as err:
                # Roll back the transaction if an exception occurs
                transaction.rollback()
                raise RuntimeError(f"Error when execute SQL {query} to RDBMS. Message: {err}") from err

            # connection.commit()

    def count_table_length(self, table_name: str) -> int:
        """
        Count number of rows in a table
        :param table_name:
        :return:
        """
        engine = self._create_engine()
        table = self._get_metadata(engine).tables[self._get_actual_table_name(table_name)]
        with engine.connect() as connection:
            count_query = select(func.count().label("row_count")).select_from(table)
            result = connection.execute(count_query)
            return result.scalar()

    def count_query_length(self, query: str) -> int:
        """
        Count number of rows returned by a SQL query with a selector
        :param query:
        :return:
        """
        if self._credential.dbms == "oracle":
            count_query = f"SELECT COUNT(*) FROM ({query}) original_query"
        else:
            count_query = f"SELECT COUNT(*) FROM ({query}) AS original_query"
        query_res = self.get(count_query)
        return query_res[0][0]

    @staticmethod
    def _get_driver_for_dbms(dbms: str):
        """
        Get driver for specific DBMS
        :param dbms:
        :return:
        """
        if dbms == "postgresql":
            driver = "psycopg2"
        elif dbms == "mysql":
            driver = "mysqlconnector"
        elif dbms == "mssql":
            driver = "pyodbc"
        else:
            raise ValueError(
                f"DBMS '{dbms}' is not supported. Current supported DBMS: sqlite, postgresql, mysql, mssql"
            )
        return f"{dbms}+{driver}"

    def get_by_page_with_type(self, table_name: str, pagination: DataSourcePagination | None = None):
        """
        Get rows from database by pagination
        """
        engine = self._create_engine()

        with engine.connect() as conn:
            actual_table_name = self._get_actual_table_name(table_name)
            table = self._get_metadata(engine).tables[actual_table_name]

            if pagination is None:
                logger.info(f"page is None, get all data from table {actual_table_name}")
                query = select(table)
            elif self._credential.dbms in ("mssql", "oracle"):
                # both need an explicit ORDER BY for a stable OFFSET/FETCH - get_by_page_with_query
                # already treats them symmetrically for the same reason.
                ordering_column = table.primary_key.columns.values() if table.primary_key else [next(iter(table.c))]
                query = select(table).order_by(*ordering_column).offset(pagination.skip).limit(pagination.limit)
            else:
                query = select(table).offset(pagination.skip).limit(pagination.limit)

            result = conn.execute(query).fetchall()
            return [dict(row._mapping) for row in result]

    def get_by_page_with_query(self, original_query: str, pagination: DataSourcePagination | None = None):
        """
        Get rows from database by pagination with SQL query

        Args:
            original_query: SQL query string
            pagination: Pagination settings

        Returns:
            List of dictionaries containing the query results
        """
        if pagination is None:
            logger.info(f"page is None, get all data from query {original_query}")
            result = self.get(original_query)
            # Use _mapping attribute for SQLAlchemy 2.0 Row objects
            return [dict(row._mapping) if hasattr(row, "_mapping") else dict(row) for row in result]

        if self._credential.dbms == "mssql":
            # mssql OFFSET require ORDER BY -> hard code ORDER BY the first column
            pagination_query = (
                f"SELECT * FROM ({original_query}) AS original_query "
                f"ORDER BY 1 OFFSET {pagination.skip} ROWS FETCH NEXT {pagination.limit} ROWS ONLY"
            )
            result = self.get(pagination_query)
        elif self._credential.dbms == "oracle":
            pagination_query = (
                f"SELECT * FROM ({original_query}) original_query "
                f"ORDER BY 1 OFFSET {pagination.skip} ROWS FETCH FIRST {pagination.limit} ROWS ONLY"
            )
            result = self.get(pagination_query)
        else:
            pagination_query = (
                f"SELECT * FROM ({original_query}) AS original_query LIMIT {pagination.limit} OFFSET {pagination.skip}"
            )
            result = self.get(pagination_query)

        # Handle both SQLAlchemy 1.x and 2.x Row objects
        return [dict(row._mapping) if hasattr(row, "_mapping") else dict(row) for row in result]

    def get_random_rows_by_columns(self, table_name: str, column_names: list[str]) -> list[tuple]:
        """Fetch the given columns for a <reference> in a stable order, preserving row-tuple
        integrity. The reference task does the distinct/with-replacement sampling deterministically
        via DataSourceRegistry.get_unique_data / ctx.rng (so the full column set is returned, not a
        pre-limited slice)."""
        engine = self._create_engine()

        with engine.connect() as conn:
            actual_table_name = self._get_actual_table_name(table_name)
            table = self._get_metadata(engine).tables[actual_table_name]
            columns = [table.c[name] for name in column_names]
            # ORDER BY the selected columns (NOT random): a stable input order so the seeded
            # shuffle in get_unique_data is reproducible run-to-run. ORDER BY random() would
            # destroy that reproducibility.
            # fetch-all + sort suits reference/lookup tables; a huge source would want
            # SELECT DISTINCT or DB-side sampling — an EE-scale concern, not CE's reference path.
            return [tuple(row) for row in conn.execute(select(*columns).order_by(*columns)).fetchall()]

    def insert(self, table_name: str, data_list: list):
        """
        Insert data into table
        :param table_name:
        :param data_list:
        :return:
        """
        engine = self._create_engine()
        actual_table_name = self._get_actual_table_name(table_name)

        # Reflect the table schema from the database
        table = self._get_metadata(engine).tables[actual_table_name]

        if not data_list:
            return

        data_list = self._apply_global_json_config(data_list)
        # A whole entity bound into a scalar column (the legacy toString() idiom, e.g.
        # <key script="person"> into a varchar field) has no driver-level binding otherwise -
        # confirmed this raises hard today (sqlite3.ProgrammingError: type not supported), so
        # this only turns a crash into a correct write, never changes behavior for what works now.
        data_list = [{k: stringify_if_entity(v) for k, v in row.items()} for row in data_list]

        with engine.begin() as connection:
            try:
                connection.execute(table.insert(), data_list)
            except Exception as err:
                raise RuntimeError(f"Error when writing data to RDBMS: {err}") from err

    def _table_and_pk(self, engine, table_name: str):
        """Reflected table + its primary-key column names. update/upsert/delete key on the PK;
        a table without one is a configuration error (never silently fall back to insert)."""
        table = self._get_metadata(engine).tables[self._get_actual_table_name(table_name)]
        pk = [c.name for c in table.primary_key.columns]
        if not pk:
            raise ValueError(f"Table '{table_name}' has no primary key - update/upsert/delete need one to match rows")
        return table, pk

    @staticmethod
    def _pk_clause(table, row: dict, pk: list[str], table_name: str, operation: str):
        missing = [k for k in pk if k not in row]
        if missing:
            raise ValueError(f"{operation} on '{table_name}' requires primary-key value(s) {missing} in each record")
        return [table.c[k] == row[k] for k in pk]

    def update(self, table_name: str, data_list: list) -> int:
        """UPDATE each record by primary key; returns the number of matched rows.
        Row-by-row statements: test-data volumes, not a bulk path."""
        if not data_list:
            return 0
        engine = self._create_engine()
        table, pk = self._table_and_pk(engine, table_name)
        matched = 0
        with engine.begin() as connection:
            for row in self._apply_global_json_config(data_list):
                values = {k: v for k, v in row.items() if k not in pk}
                if not values:
                    raise ValueError(f"update on '{table_name}' has no non-key columns to set")
                clause = self._pk_clause(table, row, pk, table_name, "update")
                matched += connection.execute(table.update().where(*clause).values(**values)).rowcount
        return matched

    def upsert(self, table_name: str, data_list: list) -> None:
        """UPDATE by primary key, INSERT the rows that matched nothing."""
        if not data_list:
            return
        engine = self._create_engine()
        table, pk = self._table_and_pk(engine, table_name)
        with engine.begin() as connection:
            for row in self._apply_global_json_config(data_list):
                clause = self._pk_clause(table, row, pk, table_name, "upsert")
                values = {k: v for k, v in row.items() if k not in pk}
                if values:
                    exists = connection.execute(table.update().where(*clause).values(**values)).rowcount > 0
                else:  # all-PK row: nothing to update, just ensure presence
                    exists = connection.execute(select(table.c[pk[0]]).where(*clause)).first() is not None
                if not exists:
                    connection.execute(table.insert(), [row])

    def delete(self, table_name: str, data_list: list) -> int:
        """DELETE each record by primary key; returns the number of deleted rows."""
        if not data_list:
            return 0
        engine = self._create_engine()
        table, pk = self._table_and_pk(engine, table_name)
        deleted = 0
        with engine.begin() as connection:
            for row in self._apply_global_json_config(data_list):
                clause = self._pk_clause(table, row, pk, table_name, "delete")
                deleted += connection.execute(table.delete().where(*clause)).rowcount
        return deleted

    def _get_actual_table_name(self, table_name: str) -> str:
        """
        Get actual table name (for match-case)
        :param table_name:
        :return:
        """
        inspector = inspect(self._create_engine())
        tables_in_db = inspector.get_table_names(schema=self._credential.db_schema)
        actual_table_name = next(
            (table for table in tables_in_db if table.lower() == table_name.lower()),
            None,
        )

        if actual_table_name is None:
            raise ValueError(f"Table '{table_name}' not found in the database.")

        return f"{self._credential.db_schema}.{actual_table_name}" if self._credential.db_schema else actual_table_name

    def _split_sequence_schema(self, sequence_name: str, default_schema: str) -> tuple[str, str]:
        """A dotted name ('zsv.t_angebote_id_seq', explicit sequence= from the DSL) carries its
        own schema - splitting here keeps every sequence query below two-part; blindly
        prepending the credential schema would build a malformed 3-part identifier."""
        if "." in sequence_name:
            schema, sequence_name = sequence_name.split(".", 1)
            return schema, sequence_name
        return default_schema, sequence_name

    @staticmethod
    def _quoted_qualified_identifier(dialect: Dialect, *parts: str) -> str:
        """Quote every identifier component with the active SQL dialect.

        DDL cannot bind identifiers as values. Keeping the interpolation in this one
        dialect-aware seam prevents sequence and table names from becoming executable SQL.
        """
        if not parts or any(not part for part in parts):
            raise ValueError("SQL identifiers must be non-empty")
        preparer = cast(Any, dialect).identifier_preparer
        quote = preparer.quote_identifier
        return ".".join(quote(part) for part in parts)

    def get_current_sequence_number(
        self, sequence_name: str, table_name: str | None = None, column_name: str | None = None
    ) -> int:
        """
        Get the current value of a database sequence: atomically advance it by 1 and return the
        new value (same contract as Postgres nextval).

        Supported for postgresql and mysql. mssql/oracle are not supported yet: prototyped with
        native sequences, but SequenceTableGenerator is re-instantiated per page/scan-phase pass
        (existing engine behavior) and each instantiation calls this side-effecting method, which
        was observed to produce colliding id ranges against MSSQL non-deterministically - needs a
        fix to that interaction, not just a dialect-specific SQL port.
        :param sequence_name: Name of the sequence
        :param table_name: MySQL only - the target table (convention case, unset for an explicit
            sequence= name). MySQL has no freestanding sequence object, so it integrates directly
            with the target table's own AUTO_INCREMENT counter instead - the only way a
            MySQL-backed id column stays coherent with plain (non-generator) inserts into the
            same table, mirroring why Postgres's native sequence already works this way.
        :param column_name: MySQL only - the target column (paired with table_name).
        :return: Current sequence number
        """
        dbms = self._credential.dbms
        with self._create_engine().connect() as connection:
            transaction = connection.begin()
            try:
                if dbms == "postgresql":
                    schema, seq = self._split_sequence_schema(sequence_name, self._credential.db_schema or "public")
                    qualified_sequence = self._quoted_qualified_identifier(connection.dialect, schema, seq)
                    exists = connection.execute(
                        text(
                            "SELECT EXISTS (SELECT 1 FROM pg_sequences "
                            "WHERE schemaname = :schema AND sequencename = :seq_name)"
                        ),
                        {"schema": schema, "seq_name": seq},
                    ).scalar()
                    if not exists:
                        connection.execute(text(f"CREATE SEQUENCE IF NOT EXISTS {qualified_sequence}"))
                    current_value = connection.execute(
                        text("SELECT nextval(CAST(:sequence_name AS regclass))"),
                        {"sequence_name": qualified_sequence},
                    ).scalar()
                elif dbms == "mysql":
                    current_value = self._advance_mysql_auto_increment(
                        connection, sequence_name, table_name, column_name, 1
                    )
                else:
                    # mssql/oracle: native-sequence support was prototyped and pulled - a
                    # per-page/scan-phase re-instantiation of SequenceTableGenerator (existing
                    # DATAMIMIC behavior, not new) calls this method multiple times per statement
                    # with side-effecting advances, and the resulting id ranges were observed to
                    # collide non-deterministically against MSSQL. Needs a fix to the range
                    # arithmetic (or the scan-phase call pattern) before shipping, not just a
                    # dialect-specific SQL port. See PR discussion.
                    raise ValueError(f"SequenceTableGenerator is not supported for dbms '{dbms}'")
                transaction.commit()
                return current_value
            except Exception as err:
                transaction.rollback()
                logger.error(f"Failed to get current sequence number for {sequence_name}: {err}")
                raise

    def increase_sequence_number(
        self,
        sequence_name: str,
        increment: int = 1,
        table_name: str | None = None,
        column_name: str | None = None,
    ) -> None:
        """
        Atomically advance the sequence by `increment` (a single atomic statement/lock-scoped
        update per dialect - never a read-current-value-then-write-it-back-in-Python round trip,
        which would race under the concurrent, multiprocess callers this generator exists for).
        :param sequence_name: Name of the sequence
        :param increment: Increment value
        :param table_name: MySQL only - see get_current_sequence_number.
        :param column_name: MySQL only - see get_current_sequence_number.
        """
        increment = int(increment)  # callers may pass a raw XML attribute string (e.g. count=)
        dbms = self._credential.dbms
        with self._create_engine().connect() as connection:
            transaction = connection.begin()
            try:
                if dbms == "postgresql":
                    schema, seq = self._split_sequence_schema(sequence_name, self._credential.db_schema or "public")
                    qualified_sequence = self._quoted_qualified_identifier(connection.dialect, schema, seq)
                    connection.execute(
                        text(
                            "SELECT setval(CAST(:sequence_name AS regclass), "
                            "nextval(CAST(:sequence_name AS regclass)) + :increment)"
                        ),
                        {"sequence_name": qualified_sequence, "increment": increment},
                    )
                elif dbms == "mysql":
                    self._advance_mysql_auto_increment(connection, sequence_name, table_name, column_name, increment)
                else:
                    # See get_current_sequence_number - mssql/oracle native-sequence support
                    # pulled pending a fix to the scan-phase re-instantiation interaction.
                    raise ValueError(f"SequenceTableGenerator is not supported for dbms '{dbms}'")
                transaction.commit()
            except Exception as err:
                transaction.rollback()
                logger.error(f"Failed to increase sequence number for {sequence_name}: {err}")
                raise

    def _advance_mysql_auto_increment(
        self, connection, sequence_name: str, table_name: str | None, column_name: str | None, increment: int
    ) -> int:
        """MySQL has no freestanding sequence object (pre-MariaDB) - AUTO_INCREMENT is a
        per-table column property, not an independently nameable thing. The only way a
        MySQL-backed id column stays coherent with OTHER, non-generator inserts into the same
        table (the same guarantee Postgres's native sequence gives for free, since a generator
        there advances the exact object the column's own DEFAULT already points at)
        is to advance that table's real AUTO_INCREMENT counter directly - not a separate,
        unrelated counter table, which two independent counters could never keep in sync.

        Only supported for the convention-derived case (table_name/column_name known - a bare
        `generator="SequenceTableGenerator"`, no explicit sequence=): an explicit legacy
        sequence= name has no MySQL object to bind to, so it's a clear error rather than a
        silently-wrong separate counter.

        `information_schema.TABLES.AUTO_INCREMENT` alone is NOT reliable: it's served from
        InnoDB's persistent statistics cache, refreshed only every `innodb_stats_auto_recalc`
        threshold or `information_schema_stats_expiry` seconds (default 86400 = 24h). A plain
        INSERT elsewhere doesn't force a refresh, so a stale read can return a LOWER value than
        the table's real counter - handing out ids that collide with rows already inserted
        by other means. `SET SESSION information_schema_stats_expiry = 0` forces this session's
        read to bypass the cache and reflect the live value; it's session-scoped, so it doesn't
        need any privilege beyond what this connection already has and doesn't affect other
        sessions. GET_LOCK/RELEASE_LOCK are session-scoped advisory locks, independent of
        transactions/DDL (ALTER TABLE ... AUTO_INCREMENT=n is DDL, not itself atomic against a
        concurrent read-then-write), so they serialize concurrent callers around the whole
        read-then-ALTER round trip safely.
        """
        if table_name is None or column_name is None:
            raise ValueError(
                f"SequenceTableGenerator(sequence='{sequence_name}') is not supported for MySQL: MySQL has no "
                "freestanding sequence object to bind an explicit name to. Omit sequence= to use the target "
                "table's own AUTO_INCREMENT column instead."
            )
        schema = self._credential.db_schema
        table = self._quoted_qualified_identifier(
            connection.dialect,
            *((schema, table_name) if schema else (table_name,)),
        )
        lock_name = f"datamimic_seq_{schema}_{table_name}_{column_name}"[:64]
        acquired = connection.execute(text("SELECT GET_LOCK(:name, 30)"), {"name": lock_name}).scalar()
        if acquired != 1:
            raise RuntimeError(f"Could not acquire MySQL advisory lock for sequence '{sequence_name}' within 30s")
        try:
            connection.execute(text("SET SESSION information_schema_stats_expiry = 0"))
            next_value = connection.execute(
                text(
                    "SELECT AUTO_INCREMENT FROM information_schema.TABLES "
                    "WHERE table_schema = :schema AND table_name = :table"
                ),
                {"schema": schema, "table": table_name},
            ).scalar()
            next_value = int(next_value or 1)
            connection.execute(text(f"ALTER TABLE {table} AUTO_INCREMENT = {next_value + int(increment)}"))
            return next_value
        finally:
            try:
                connection.execute(text("SELECT RELEASE_LOCK(:name)"), {"name": lock_name})
            except Exception as release_err:
                # Never let a lock-release failure mask the original error (or a successful
                # result) from the try block above - just log it. The advisory lock is
                # session-scoped anyway, so it's released automatically once this connection
                # closes even if RELEASE_LOCK itself fails here.
                logger.error(f"Failed to release MySQL advisory lock '{lock_name}': {release_err}")

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._engine:
            self._engine.dispose()
