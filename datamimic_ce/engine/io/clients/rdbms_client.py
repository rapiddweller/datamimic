# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import copy
import logging
import sys
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from enum import StrEnum
from pathlib import Path
from typing import Protocol, runtime_checkable
from urllib.parse import quote

import sqlalchemy
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    LargeBinary,
    MetaData,
    Numeric,
    Table,
    Text,
    func,
    inspect,
    select,
    text,
)
from sqlalchemy.dialects import registry
from sqlalchemy.engine import Connection, Dialect, Engine
from sqlalchemy.engine.default import DefaultDialect
from sqlalchemy.engine.row import Row
from sqlalchemy.pool import QueuePool
from sqlalchemy.schema import CreateTable
from sqlalchemy.types import TypeEngine

from datamimic_ce.engine.dsl.vocabulary.enums.dbms_enums import Dbms

# isort: split
import datamimic_ce.engine.io.clients.sql_dialect as sql_dialect
from datamimic_ce.engine.io.clients.database_client import DatabaseClient
from datamimic_ce.engine.io.clients.entity_serialization import stringify_entity_value
from datamimic_ce.engine.io.connection_config.rdbms_connection_config import RdbmsConnectionConfig, sqlite_database_path
from datamimic_ce.engine.io.contracts import ColumnKind as ColumnKind
from datamimic_ce.engine.io.contracts import DataSourcePagination
from datamimic_ce.engine.io.contracts import column_kind_of_type as column_kind_of_type
from datamimic_ce.errors import IssueCode, NormalizedDbError, OperationError, client_config_error, operation_error

logger = logging.getLogger("DATAMIMIC")

_TRUNCATE_DIALECTS = frozenset({"postgresql", "mssql"})  # SQLAlchemy dialect names


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
    "read_only",
}

# <execute> scripts are raw SQL: no bind parameters (":new" in a trigger) and no DBAPI percent formatting ("g % 3")
_RAW_SCRIPT = {"no_parameters": True}


@contextmanager
def _normalize_database_errors(target: str) -> Iterator[list[OperationError]]:
    """Normalize database failures without retaining their statements or driver messages."""
    failures: list[OperationError] = []
    try:
        yield failures
    except sqlalchemy.exc.SQLAlchemyError as error:
        failures.append(_operation_failure(target, error))


class RdbmsClient(DatabaseClient):
    def __init__(self, credential: RdbmsConnectionConfig, task_id: str | None = None):
        self._credential = credential
        self._engine: Engine | None = None
        self._read_only_engine: Engine | None = None
        self._task_id = task_id
        self._columns_by_selector: dict[str, list[str]] = {}

        # Keep only real SQLAlchemy create_engine kwargs. The connection config allows extra keys
        # (env files carry connection identity like dbms/host plus vendor knobs such as legacy
        # clean/catalog/quoteTableNames); anything not a create_engine parameter would raise, so allowlist.
        all_config = credential.get_connection_config()
        self._engine_kwargs = {k: v for k, v in all_config.items() if k in _ENGINE_KWARGS}
        if credential.read_only:
            # Autocommit would bypass backend transaction read-only enforcement.
            self._engine_kwargs["isolation_level"] = "SERIALIZABLE"
            self._engine_kwargs.pop("execution_options", None)
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
    def engine(self) -> Engine | None:
        return self._engine

    @engine.setter
    def engine(self, value: Engine | None) -> None:
        self._engine = value

    def _new_engine(self, url: str, **kwargs: object) -> Engine:
        try:
            return sqlalchemy.create_engine(url, **kwargs)
        except TypeError as error:
            raise client_config_error(
                code=IssueCode.CLIENT_PREFLIGHT_INVALID_CONFIGURATION,
                client_id="database",
                kind=self._credential.dbms.value,
                reason="unsupported SQLAlchemy engine option or value",
            ) from error

    def _create_engine(self) -> Engine:
        """
        Create SQLAlchemy engine based on provided credentials and database management system (DBMS).
        :return: SQLAlchemy engine instance
        """
        # Return the existing engine if it has already been created
        if self._engine is not None:
            self._configure_read_only_engine()
            return self._engine

        # Extract database credentials and parameters
        dbms = self._credential.dbms
        if self._credential.read_only and dbms is Dbms.MSSQL:
            raise operation_error(
                code=IssueCode.OPERATION_READ_ONLY_WRITE_BLOCKED,
                target="database connection",
                reason="SQL Server read-only transactions are not supported",
            )
        db = self._credential.database
        user = None if self._credential.user is None else quote(self._credential.user)
        password = None if self._credential.password is None else quote(self._credential.password)
        host = self._credential.host
        port = self._credential.port

        def create_sqlite_engine(file_path: Path) -> Engine:
            """
            Create an SQLite engine.
            :param file_path: Path to the SQLite database file
            :return: SQLAlchemy engine for SQLite
            """
            logger.info(f"Using SQLite database at {file_path}")
            if self._credential.read_only:
                return self._new_engine(
                    f"sqlite:///file:{quote(file_path.resolve().as_posix(), safe='/')}?mode=ro&uri=true",
                    **self._engine_kwargs,
                )
            return self._new_engine(f"sqlite:///{file_path}", **self._engine_kwargs)

        def create_sqlalchemy_engine(
            driver: str, user: str | None, password: str | None, host: str | None, port: int | None, db: str
        ) -> Engine:
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
            return self._new_engine(
                f"{driver}://{user}:{password}@{host}:{port}/{db}",
                poolclass=QueuePool,
                **self._engine_kwargs,
            )

        # Match the DBMS type and create the appropriate SQLAlchemy engine
        match dbms:
            case Dbms.SQLITE:
                if not self._task_id:
                    raise ValueError("Task ID is required to create SQLite db in task folder")
                # Both allowed runtime environments use a SQLite file inside the task folder.
                db_path = sqlite_database_path(db)
                if not db_path.exists() and self._credential.read_only:
                    raise operation_error(
                        code=IssueCode.OPERATION_READ_ONLY_WRITE_BLOCKED,
                        target="SQLite connection",
                        reason="read-only database must already exist",
                    )
                if not db_path.exists():
                    logger.info(f"Creating SQLite db file in task folder: {db_path}")
                    db_path.parent.mkdir(parents=True, exist_ok=True)
                self._engine = create_sqlite_engine(db_path)

            case Dbms.MSSQL:
                # ODBC Driver 17 (pyodbc) is the default; opt into the pure-Python pymssql/FreeTDS
                # driver with driver="pymssql" on the <database> credential - no proprietary MS
                # ODBC package to install, avoids the exact driver-install friction that pushed
                # DATAMIMIC EE to make pymssql its own default (rdbms/url_builder.py).
                extra_config = self._credential.model_extra or {}
                if extra_config.get("driver") == "pymssql":
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

            case Dbms.ORACLE:
                # Set OracleDB version and import the necessary module
                import oracledb

                oracledb.version = "8.3.0"
                sys.modules["cx_Oracle"] = oracledb
                self._engine = create_sqlalchemy_engine(dbms, user, password, host, port, f"?service_name={db}")

            case _:
                # For other DBMS types, use a generic method to get the driver and create the engine
                driver = RdbmsClient._get_driver_for_dbms(dbms)
                self._engine = create_sqlalchemy_engine(driver, user, password, host, port, db)

        self._configure_read_only_engine()
        return self._engine

    def _require_write(self, operation: str) -> None:
        if self._credential.read_only:
            raise operation_error(
                code=IssueCode.OPERATION_READ_ONLY_WRITE_BLOCKED, target=operation, reason="connection is read-only"
            )

    def _require_read_query(self, query: str) -> None:
        if self._credential.read_only:
            sql_dialect.require_read_only_query(query, self._credential.dbms)

    @property
    def dbms(self) -> Dbms:
        return self._credential.dbms

    def _configure_read_only_engine(self) -> None:
        if not self._credential.read_only or self._engine is self._read_only_engine:
            return
        dbms = self._credential.dbms
        if dbms is Dbms.MSSQL:
            raise operation_error(
                code=IssueCode.OPERATION_READ_ONLY_WRITE_BLOCKED,
                target="database connection",
                reason="SQL Server read-only transactions are not supported",
            )

        def begin_read_only(connection):
            command = "PRAGMA query_only = ON" if dbms is Dbms.SQLITE else "SET TRANSACTION READ ONLY"
            connection.exec_driver_sql(command)

        sqlalchemy.event.listen(self._engine, "begin", begin_read_only)
        self._read_only_engine = self._engine

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
        extra_config = self._credential.model_extra or {}
        none_as_null_col_value = extra_config.get("none_as_null_col", "")
        if not isinstance(none_as_null_col_value, str):
            raise TypeError("none_as_null_col must be a comma-separated string")
        none_as_null_col = [col.strip() for col in none_as_null_col_value.split(",") if col.strip()]
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
        self._require_read_query(query)
        try:
            # Establish a database connection
            with self._create_engine().connect() as connection:
                executable_query = sqlalchemy.text(query)
                result = connection.execute(executable_query)
                # Fetch all rows
                rows = result.fetchall()

            return rows
        except sqlalchemy.exc.SQLAlchemyError as error:
            failure = _operation_failure("database read", error)
        raise failure

    def execute_sql_script(self, query: str) -> None:
        """
        Execute a SQL query without returning any result
        :param query:
        :return:
        """
        self._require_write("execute_sql_script")
        if query is None:
            return
        failure: OperationError | None = None
        try:
            with self._create_engine().connect() as connection, connection.begin():
                for command in sql_dialect.split_script(query, self._credential.dbms):
                    connection.exec_driver_sql(command, execution_options=_RAW_SCRIPT)
        except sqlalchemy.exc.SQLAlchemyError as error:
            failure = _operation_failure("SQL script", error)
        if failure is not None:
            raise failure

    def count_table_length(self, table_name: str) -> int:
        """
        Count number of rows in a table
        :param table_name:
        :return:
        """
        try:
            engine = self._create_engine()
            table = self._get_metadata(engine).tables[self._get_actual_table_name(table_name)]
            with engine.connect() as connection:
                count_query = select(func.count().label("row_count")).select_from(table)
                result = connection.execute(count_query)
                return result.scalar_one()
        except sqlalchemy.exc.SQLAlchemyError as error:
            failure = _operation_failure("database source count", error)
        raise failure

    def count_query_length(self, query: str) -> int:
        """
        Count number of rows returned by a SQL query with a selector
        :param query:
        :return:
        """
        self._require_read_query(query)
        count_query = sql_dialect.count_query(query, self._credential.dbms)
        query_res = self.get(count_query)
        return query_res[0][0]

    @staticmethod
    def _get_driver_for_dbms(dbms: Dbms):
        """
        Get driver for specific DBMS
        :param dbms:
        :return:
        """
        if dbms is Dbms.POSTGRESQL:
            driver = "psycopg2"
        elif dbms is Dbms.MYSQL:
            driver = "mysqlconnector"
        elif dbms is Dbms.MSSQL:
            driver = "pyodbc"
        else:
            raise ValueError(f"DBMS '{dbms}' has no generic SQLAlchemy driver")
        return f"{dbms}+{driver}"

    def get_by_page_with_type(self, table_name: str, pagination: DataSourcePagination | None = None):
        """Rows of a table, ordered by its primary key, else by every column. For a stable snapshot that
        order keeps OFFSET pages disjoint across pages and workers, and keeps full reads that are sliced
        or shuffled per worker (random/cumulated/unique) identical in every worker."""
        with _normalize_database_errors("database read") as failures:
            engine = self._create_engine()

            with engine.connect() as conn:
                actual_table_name = self._get_actual_table_name(table_name)
                table = self._get_metadata(engine).tables[actual_table_name]

                query = select(table).order_by(*(table.primary_key.columns or table.c))
                if pagination is None:
                    logger.info(f"page is None, get all data from table {actual_table_name}")
                else:
                    query = query.offset(pagination.skip).limit(pagination.limit)

                result = conn.execute(query).fetchall()
                return [dict(row._mapping) for row in result]
        if failures:
            raise failures[0]

    def get_by_page_with_query(self, original_query: str, pagination: DataSourcePagination | None = None):
        """
        Get rows from database by pagination with SQL query

        Args:
            original_query: SQL query string
            pagination: Pagination settings

        Returns:
            List of dictionaries containing the query results
        """
        self._require_read_query(original_query)
        if pagination is None:
            logger.info("page is None, get all data from query")
            result = self.get(original_query)
            # Use _mapping attribute for SQLAlchemy 2.0 Row objects
            return [dict(row._mapping) if isinstance(row, Row) else dict(row) for row in result]

        page = sql_dialect.selector_page(
            original_query,
            self._credential.dbms,
            pagination.skip,
            pagination.limit,
            self._selector_columns(original_query),
        )
        result = self.get(page.sql)[page.rows]

        # Handle both SQLAlchemy 1.x and 2.x Row objects
        return [dict(row._mapping) if isinstance(row, Row) else dict(row) for row in result]

    def _selector_columns(self, query: str) -> list[str]:
        """Output column names of a selector, probed once per selector rather than once per page."""
        self._require_read_query(query)
        if query not in self._columns_by_selector:
            failure: OperationError | None = None
            try:
                probe = text(sql_dialect.column_probe_query(query, self._credential.dbms))
                with self._create_engine().connect() as connection:
                    self._columns_by_selector[query] = list(connection.execute(probe).keys())
            except sqlalchemy.exc.SQLAlchemyError as error:
                failure = _operation_failure("database selector", error)
            if failure is not None:
                raise failure
        return self._columns_by_selector[query]

    def get_random_rows_by_columns(self, table_name: str, column_names: list[str]) -> list[tuple]:
        """Fetch the given columns for a <reference> in a stable order, preserving row-tuple
        integrity. The reference task does the distinct/with-replacement sampling deterministically
        via runtime source selection / ctx.rng (so the full column set is returned, not a
        pre-limited slice)."""
        with _normalize_database_errors("database read") as failures:
            engine = self._create_engine()

            with engine.connect() as conn:
                actual_table_name = self._get_actual_table_name(table_name)
                table = self._get_metadata(engine).tables[actual_table_name]
                columns = [table.c[name] for name in column_names]
                # ORDER BY the selected columns (NOT random): a stable input order so the seeded
                # shuffle is reproducible run-to-run. ORDER BY random() would
                # destroy that reproducibility.
                # fetch-all + sort suits reference/lookup tables; a huge source would want
                # SELECT DISTINCT or DB-side sampling — an EE-scale concern, not CE's reference path.
                return [tuple(row) for row in conn.execute(select(*columns).order_by(*columns)).fetchall()]
        if failures:
            raise failures[0]

    def insert(self, table_name: str, data_list: list):
        """
        Insert data into table
        :param table_name:
        :param data_list:
        :return:
        """
        self._require_write("insert")
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
        data_list = [{k: stringify_entity_value(v) for k, v in row.items()} for row in data_list]

        with engine.begin() as connection:
            try:
                connection.execute(table.insert(), data_list)
                return
            except sqlalchemy.exc.SQLAlchemyError as err:
                failure = _operation_failure("database write", err)
            raise failure

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
        with _normalize_database_errors("database write") as failures:
            self._require_write("update")
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
        if failures:
            raise failures[0]

    def upsert(self, table_name: str, data_list: list) -> None:
        """UPDATE by primary key, INSERT the rows that matched nothing."""
        with _normalize_database_errors("database write") as failures:
            self._require_write("upsert")
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
        if failures:
            raise failures[0]

    def delete(self, table_name: str, data_list: list) -> int:
        """DELETE each record by primary key; returns the number of deleted rows."""
        with _normalize_database_errors("database write") as failures:
            self._require_write("delete")
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
        if failures:
            raise failures[0]

    def clear_table(self, table_name: str) -> None:
        """Remove every row and keep the table, its indexes and constraints (target="db.clear").

        PostgreSQL and MSSQL use TRUNCATE and fall back to a full-table DELETE when the database refuses it;
        other dialects use DELETE. A successful TRUNCATE reports no row count."""
        self._require_write("clear")
        engine = self._create_engine()
        table = self._get_metadata(engine).tables[self._get_actual_table_name(table_name)]
        failure: OperationError | None = None
        try:
            backend_action, deleted = self._truncate_or_delete_all(engine, table)
        except sqlalchemy.exc.SQLAlchemyError as err:
            failure = _operation_failure("rdbms.clear", err)
        if failure is not None:
            raise failure
        logger.info(
            "OPERATION | rdbms.clear | table=%s | action=clear | backend_action=%s | deleted_count=%s",
            table.name,
            backend_action,
            "unavailable" if deleted is None else deleted,
        )

    def ensure_table(
        self, entity: str, columns: tuple[tuple[str, ColumnKind], ...], primary_key: tuple[str, ...]
    ) -> None:
        """Create the table when no table of that name exists (createTable); never alter or drop one.

        An existing table must have every written column and the same primary key, else the run fails with I930. The
        table name lookup ignores case, as the row writes do; column names compare exactly."""
        self._require_write("createTable")
        engine = self._create_engine()
        schema = self._credential.db_schema
        table = create_table_definition(entity, columns, primary_key, schema)
        failure: OperationError | None = None
        try:
            existing = self._find_table_name(entity)
            if existing is None:
                table.create(engine, checkfirst=True)
                logger.info("OPERATION | rdbms.create_table | table=%s | action=created", table.fullname)
                return
            reflected = Table(existing, MetaData(), autoload_with=engine, schema=schema)
        except sqlalchemy.exc.SQLAlchemyError as error:
            failure = _operation_failure("rdbms.create_table", error)
        if failure is not None:
            raise failure
        difference = table_difference(table, reflected)
        if difference is not None:
            raise operation_error(
                code=IssueCode.OPERATION_TABLE_DRIFT, target=reflected.fullname, difference=difference
            )
        logger.info("OPERATION | rdbms.create_table | table=%s | action=exists", reflected.fullname)

    @staticmethod
    def _truncate_or_delete_all(engine, table) -> tuple[str, int | None]:
        if engine.dialect.name in _TRUNCATE_DIALECTS:
            # A refused TRUNCATE (e.g. a foreign key references the table) falls through to the DELETE below.
            with suppress(sqlalchemy.exc.SQLAlchemyError), engine.begin() as connection:
                connection.execute(text(f"TRUNCATE TABLE {engine.dialect.identifier_preparer.format_table(table)}"))
                return "truncate", None
        with engine.begin() as connection:
            return "delete_all", connection.execute(table.delete()).rowcount

    def _find_table_name(self, table_name: str) -> str | None:
        """The name of the table in the database that matches ``table_name`` without case; None when none does."""
        inspector = inspect(self._create_engine())
        tables_in_db = inspector.get_table_names(schema=self._credential.db_schema)
        return next((table for table in tables_in_db if table.lower() == table_name.lower()), None)

    def _get_actual_table_name(self, table_name: str) -> str:
        """
        Get actual table name (for match-case)
        :param table_name:
        :return:
        """
        actual_table_name = self._find_table_name(table_name)
        if actual_table_name is None:
            native_error = ValueError(f"Table '{table_name}' not found in the database.")
            raise operation_error(
                code=IssueCode.OPERATION_EXECUTION_FAILED,
                target="database table lookup",
                error=NormalizedDbError(None, DbErrorCategory.TABLE_NOT_FOUND, "Requested table is unavailable"),
            ) from native_error

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
        if not isinstance(dialect, DefaultDialect):
            raise TypeError("SQLAlchemy dialect does not provide identifier quoting")
        preparer = dialect.identifier_preparer
        quote = preparer.quote_identifier
        return ".".join(quote(part) for part in parts)

    def get_current_sequence_number(
        self, sequence_name: str, table_name: str | None = None, column_name: str | None = None
    ) -> int:
        """Take one sequence value and return it."""
        return self.reserve_sequence_block(sequence_name, 1, table_name, column_name)

    def increase_sequence_number(
        self,
        sequence_name: str,
        increment: int = 1,
        table_name: str | None = None,
        column_name: str | None = None,
    ) -> None:
        """Discard a block of sequence numbers (use reserve_sequence_block to receive its start)."""
        self.reserve_sequence_block(sequence_name, increment, table_name, column_name)

    def reserve_sequence_block(
        self, sequence_name: str, count: int, table_name: str | None = None, column_name: str | None = None
    ) -> int:
        """Reserve count consecutive numbers and return the first, under a per-sequence database lock."""
        with _normalize_database_errors("database sequence") as failures:
            self._require_write("reserve_sequence_block")
            count = int(count)
            if count < 1:
                raise ValueError("Sequence reservation count must be positive")
            dbms = self._credential.dbms
            if dbms is Dbms.POSTGRESQL:
                # The transaction must hold the lock even if the configured engine uses AUTOCOMMIT,
                # and catalog reads after the lock must see a sequence created by the prior holder.
                with (
                    self._create_engine().connect() as connection,
                    connection.execution_options(isolation_level="READ COMMITTED").begin(),
                ):
                    return self._reserve_postgresql_sequence(connection, sequence_name, count)
            if dbms is Dbms.MYSQL:
                with self._create_engine().begin() as connection:
                    return self._advance_mysql_auto_increment(connection, sequence_name, table_name, column_name, count)
            raise ValueError(f"SequenceTableGenerator is not supported for dbms '{dbms}'")
        raise failures[0]

    def _reserve_postgresql_sequence(self, connection: Connection, sequence_name: str, count: int) -> int:
        schema, seq = self._split_sequence_schema(sequence_name, self._credential.db_schema or "public")
        qualified_sequence = self._quoted_qualified_identifier(connection.dialect, schema, seq)
        # Cast to name before hashing so aliases due to PostgreSQL identifier truncation lock together.
        connection.execute(
            text(
                "SELECT pg_catalog.pg_advisory_xact_lock("
                "pg_catalog.hashtext('datamimic_seq:' || CAST(CAST(:schema AS name) AS text)), "
                "pg_catalog.hashtext(CAST(CAST(:seq AS name) AS text)))"
            ),
            {"schema": schema, "seq": seq},
        )
        params = {"sequence_name": qualified_sequence}
        increment = connection.execute(
            text(
                "SELECT seqincrement FROM pg_catalog.pg_sequence "
                "WHERE seqrelid = pg_catalog.to_regclass(:sequence_name)"
            ),
            params,
        ).scalar_one_or_none()
        if increment is None:
            connection.execute(text(f"CREATE SEQUENCE IF NOT EXISTS {qualified_sequence}"))
        elif increment != 1:
            raise ValueError("SequenceTableGenerator requires PostgreSQL sequences with INCREMENT BY 1")

        # Read the shared high-water mark, including all values cached by other backends.
        # nextval() on a pooled connection could return a session-local cached value below it.
        last_value, is_called = connection.execute(
            text(f"SELECT last_value, is_called FROM {qualified_sequence}")
        ).one()
        start = int(last_value) + int(is_called)
        connection.execute(
            text("SELECT pg_catalog.setval(CAST(:sequence_name AS regclass), :last_value)"),
            {**params, "last_value": start + count - 1},
        )
        return start

    def _advance_mysql_auto_increment(
        self,
        connection: Connection,
        sequence_name: str,
        table_name: str | None,
        column_name: str | None,
        increment: int,
    ) -> int:
        """Return the table's previous AUTO_INCREMENT under its session advisory lock.

        Disabling the information_schema statistics cache makes the reads see the live counter.
        ALTER TABLE implicitly commits, so a session lock spans both reads and the update.
        """
        self._require_write("_advance_mysql_auto_increment")
        if table_name is None or column_name is None:
            raise ValueError(
                f"SequenceTableGenerator(sequence='{sequence_name}') is not supported for MySQL: MySQL has no "
                "freestanding sequence object to bind an explicit name to. Omit sequence= to use the target "
                "table's own AUTO_INCREMENT column instead."
            )
        schema = self._credential.db_schema or self._credential.database
        table = self._quoted_qualified_identifier(connection.dialect, schema, table_name)
        # AUTO_INCREMENT is table-scoped. Case-fold the lock name so MySQL configurations with
        # case-insensitive identifiers cannot take distinct locks on the same table.
        lock_name = f"datamimic_seq_{schema.lower()}_{table_name.lower()}"[:64]
        try:
            acquired = connection.execute(text("SELECT GET_LOCK(:name, 30)"), {"name": lock_name}).scalar()
            if acquired != 1:
                raise RuntimeError(f"Could not acquire MySQL advisory lock for sequence '{sequence_name}' within 30s")
            connection.execute(text("SET SESSION information_schema_stats_expiry = 0"))
            # Fresh InnoDB tables can report NULL until their default counter is initialized.
            # A populated table with an unreadable counter must never be treated as fresh.
            counter_query = text(
                "SELECT CASE WHEN AUTO_INCREMENT IS NOT NULL THEN AUTO_INCREMENT "
                "WHEN EXISTS (SELECT 1 FROM information_schema.COLUMNS "
                "WHERE table_schema = :schema AND table_name = :table AND EXTRA = 'auto_increment') "
                f"AND NOT EXISTS (SELECT 1 FROM {table}) THEN 1 END "
                "FROM information_schema.TABLES "
                "WHERE table_schema = :schema AND table_name = :table"
            )
            params = {"schema": schema, "table": table_name}
            counter = connection.execute(counter_query, params).scalar_one_or_none()
            if counter is None:
                raise ValueError("SequenceTableGenerator could not read the MySQL AUTO_INCREMENT counter")
            start = int(counter)
            end = start + increment
            connection.execute(text(f"ALTER TABLE {table} AUTO_INCREMENT = {end}"))
            advanced = connection.execute(counter_query, params).scalar_one_or_none()
            if advanced is None or int(advanced) < end:
                raise ValueError("MySQL AUTO_INCREMENT counter could not reserve the requested sequence block")
            released = connection.execute(text("SELECT RELEASE_LOCK(:name)"), {"name": lock_name}).scalar()
        except BaseException:
            # Discard the session on failure so its lock cannot survive in the pool.
            # Avoid a second SQL call that could obscure the original database error.
            try:
                connection.invalidate()
            except sqlalchemy.exc.SQLAlchemyError:
                logger.error("Failed to discard the MySQL connection after a sequence reservation error")
            raise
        if released != 1:
            connection.invalidate()
            raise RuntimeError("Could not release MySQL sequence advisory lock")
        return start

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._engine:
            self._engine.dispose()


@runtime_checkable
class _HasPgCode(Protocol):
    pgcode: str | None


@runtime_checkable
class _HasSqlState(Protocol):
    sqlstate: str | None


@runtime_checkable
class _HasSqliteCode(Protocol):
    sqlite_errorcode: int


@runtime_checkable
class _HasOracleCode(Protocol):
    code: int


class DbErrorCategory(StrEnum):
    """The category names that an error shows. A message or a code that covers several causes never picks one."""

    CHECK_CONSTRAINT = "check_constraint"
    COLUMN_NOT_FOUND = "column_not_found"
    CONNECTION_FAILED = "connection_failed"
    CONSTRAINT = "constraint"
    DEADLOCK = "deadlock"
    DUPLICATE_KEY = "duplicate_key"
    FOREIGN_KEY = "foreign_key"
    FUNCTION_NOT_FOUND = "function_not_found"
    NOT_NULL = "not_null"
    PERMISSION_DENIED = "permission_denied"
    SCHEMA_NOT_FOUND = "schema_not_found"
    SQLITE_ERROR = "sqlite_error"
    SYNTAX_ERROR = "syntax_error"
    TABLE_NOT_FOUND = "table_not_found"
    TIMEOUT = "timeout"
    TYPE_MISMATCH = "type_mismatch"


_PG_CATEGORIES = {
    "42P01": DbErrorCategory.TABLE_NOT_FOUND,
    "42703": DbErrorCategory.COLUMN_NOT_FOUND,
    "3F000": DbErrorCategory.SCHEMA_NOT_FOUND,
    "42883": DbErrorCategory.FUNCTION_NOT_FOUND,
    "42601": DbErrorCategory.SYNTAX_ERROR,
    "42501": DbErrorCategory.PERMISSION_DENIED,
    "22P02": DbErrorCategory.TYPE_MISMATCH,
    "22001": DbErrorCategory.TYPE_MISMATCH,
    "23505": DbErrorCategory.DUPLICATE_KEY,
    "23502": DbErrorCategory.NOT_NULL,
    "23503": DbErrorCategory.FOREIGN_KEY,
    "23514": DbErrorCategory.CHECK_CONSTRAINT,
    "40P01": DbErrorCategory.DEADLOCK,
    "57014": DbErrorCategory.TIMEOUT,
    "08001": DbErrorCategory.CONNECTION_FAILED,
    "08006": DbErrorCategory.CONNECTION_FAILED,
}
_MYSQL_CATEGORIES = {
    1146: DbErrorCategory.TABLE_NOT_FOUND,
    1054: DbErrorCategory.COLUMN_NOT_FOUND,
    1049: DbErrorCategory.SCHEMA_NOT_FOUND,
    1305: DbErrorCategory.FUNCTION_NOT_FOUND,
    1064: DbErrorCategory.SYNTAX_ERROR,
    1044: DbErrorCategory.PERMISSION_DENIED,
    1045: DbErrorCategory.PERMISSION_DENIED,
    1062: DbErrorCategory.DUPLICATE_KEY,
    1048: DbErrorCategory.NOT_NULL,
    1452: DbErrorCategory.FOREIGN_KEY,
    1213: DbErrorCategory.DEADLOCK,
    1205: DbErrorCategory.TIMEOUT,
    2002: DbErrorCategory.CONNECTION_FAILED,
    2003: DbErrorCategory.CONNECTION_FAILED,
    2006: DbErrorCategory.CONNECTION_FAILED,
    2013: DbErrorCategory.CONNECTION_FAILED,
}
_ORACLE_CATEGORIES = {
    1: DbErrorCategory.DUPLICATE_KEY,
    60: DbErrorCategory.DEADLOCK,
    904: DbErrorCategory.COLUMN_NOT_FOUND,
    942: DbErrorCategory.TABLE_NOT_FOUND,
    933: DbErrorCategory.SYNTAX_ERROR,
    936: DbErrorCategory.SYNTAX_ERROR,
    907: DbErrorCategory.SYNTAX_ERROR,
    911: DbErrorCategory.SYNTAX_ERROR,
    1013: DbErrorCategory.TIMEOUT,
    1017: DbErrorCategory.CONNECTION_FAILED,
    1031: DbErrorCategory.PERMISSION_DENIED,
    1400: DbErrorCategory.NOT_NULL,
    1722: DbErrorCategory.TYPE_MISMATCH,
    1861: DbErrorCategory.TYPE_MISMATCH,
    2290: DbErrorCategory.CHECK_CONSTRAINT,
    2291: DbErrorCategory.FOREIGN_KEY,
    2292: DbErrorCategory.FOREIGN_KEY,
    3113: DbErrorCategory.CONNECTION_FAILED,
    3114: DbErrorCategory.CONNECTION_FAILED,
    12541: DbErrorCategory.CONNECTION_FAILED,
}
_SQLITE_CATEGORIES = {
    # One code for a missing table, a missing column and invalid SQL: none of them is named.
    1: DbErrorCategory.SQLITE_ERROR,
    3: DbErrorCategory.PERMISSION_DENIED,
    5: DbErrorCategory.TIMEOUT,
    6: DbErrorCategory.TIMEOUT,
    8: DbErrorCategory.PERMISSION_DENIED,
    14: DbErrorCategory.CONNECTION_FAILED,
    19: DbErrorCategory.CONSTRAINT,
}


# Static text, no SQL and no value: a category whose code covers several causes says what to check.
_CATEGORY_GUIDANCE: dict[str, str] = {
    DbErrorCategory.SQLITE_ERROR: (
        "SQLite reports a missing table, a missing column and invalid SQL, among other errors, alike. Check the "
        'table and column names, and the database name: database="bank" opens db/bank.sqlite, so leave the '
        ".sqlite suffix out."
    ),
}


class DriverFailure(Exception):
    """A native driver error without its message: its class name and native code, never SQL or a value."""

    driver_class: str
    native_code: str | None


def _statement_free_cause(
    error: sqlalchemy.exc.SQLAlchemyError, facts: NormalizedDbError
) -> sqlalchemy.exc.SQLAlchemyError:
    """The SQLAlchemy class without its SQL text, parameters or driver message; the driver class and code stay."""
    if isinstance(error, sqlalchemy.exc.DBAPIError):
        cause = copy.copy(error)
        cause.statement = None
        cause.params = None
        driver_failure = DriverFailure(type(error.orig).__name__)
        driver_failure.driver_class = type(error.orig).__name__
        driver_failure.native_code = facts.code
        cause.orig = driver_failure
        cause.args = (type(error).__name__,)
        return cause
    return sqlalchemy.exc.SQLAlchemyError(type(error).__name__)


def _operation_failure(target: str, error: sqlalchemy.exc.SQLAlchemyError) -> OperationError:
    """The typed failure with its statement-free cause. The caller raises it outside the except block, so the
    original error, which holds the SQL text, is neither the cause nor the context."""
    facts = _database_error_facts(error)
    failure = operation_error(
        code=IssueCode.OPERATION_EXECUTION_FAILED,
        target=target,
        error=facts,
        guidance=_CATEGORY_GUIDANCE.get(facts.category) if facts.category else None,
    )
    failure.__cause__ = _statement_free_cause(error, facts)
    return failure


def _database_error_facts(error: sqlalchemy.exc.SQLAlchemyError) -> NormalizedDbError:
    """Read driver code contracts without inspecting SQL or free-form vendor messages."""
    original = error.orig if isinstance(error, sqlalchemy.exc.DBAPIError) else error
    if isinstance(original, _HasSqliteCode):
        code = original.sqlite_errorcode
        return NormalizedDbError(str(code), _SQLITE_CATEGORIES.get(code & 0xFF), type(error).__name__)
    if "mysql.connector.errors" in sys.modules:
        from mysql.connector.errors import Error as MySqlError

        if isinstance(original, MySqlError):
            mysql_code = original.errno
            return NormalizedDbError(str(mysql_code), _MYSQL_CATEGORIES.get(mysql_code), type(error).__name__)
    if "oracledb" in sys.modules:
        from oracledb import Error as OracleError

        if isinstance(original, OracleError) and original.args and isinstance(original.args[0], _HasOracleCode):
            oracle_code = original.args[0].code
            return NormalizedDbError(
                f"ORA-{oracle_code:05d}", _ORACLE_CATEGORIES.get(oracle_code), type(error).__name__
            )
    for value in (
        original.pgcode if isinstance(original, _HasPgCode) else None,
        original.sqlstate if isinstance(original, _HasSqlState) else None,
    ):
        if isinstance(value, str) and 0 < len(value) <= 5 and value.isalnum():
            code_text = value.upper()
            return NormalizedDbError(code_text, _PG_CATEGORIES.get(code_text), type(error).__name__)
    category = DbErrorCategory.TABLE_NOT_FOUND if isinstance(error, sqlalchemy.exc.NoSuchTableError) else None
    return NormalizedDbError(None, category, type(error).__name__)


_COLUMN_TYPES: dict[ColumnKind, type[TypeEngine]] = {
    ColumnKind.TEXT: Text,
    ColumnKind.INTEGER: BigInteger,
    ColumnKind.FLOAT: Float,
    ColumnKind.DECIMAL: Numeric,
    ColumnKind.BOOLEAN: Boolean,
    ColumnKind.BINARY: LargeBinary,
    ColumnKind.DATE: Date,
    ColumnKind.DATETIME: DateTime,
}


def create_table_definition(
    entity: str, columns: tuple[tuple[str, ColumnKind], ...], primary_key: tuple[str, ...], schema: str | None = None
) -> Table:
    """The createTable table. The run creates it and Build compiles it, so both show the same columns."""
    return Table(
        entity,
        MetaData(),
        *(
            Column(name, _COLUMN_TYPES[kind], primary_key=name in primary_key, autoincrement=False)
            for name, kind in columns
        ),
        schema=schema,
    )


def create_table_ddl(table: Table, dbms: Dbms) -> str:
    """The CREATE TABLE statement for the dialect of ``dbms``, compiled without a connection."""
    statement = CreateTable(table)
    compiled = statement.compile(dialect=registry.load(dbms.value)())
    return str(compiled).strip()


def table_difference(wanted: Table, existing: Table) -> str | None:
    """The missing columns and the primary-key difference of an existing table, by exact name; None when they match.
    Extra columns are allowed (an insert leaves them to their default), and column types are not compared: SQLite
    keeps any value in any column type, and a hand-written schema often uses another type for the same data. Names
    compare exactly: an insert drops a key whose case differs from the column without an error."""
    want = {column.name for column in wanted.columns}
    have = {column.name for column in existing.columns}
    want_key = {column.name for column in wanted.primary_key.columns}
    have_key = {column.name for column in existing.primary_key.columns}
    parts = []
    if missing := sorted(want - have):
        parts.append(f"missing columns {', '.join(missing)}")
    if want_key != have_key:
        parts.append(
            f"primary key ({', '.join(sorted(have_key)) or 'none'}) instead of ({', '.join(sorted(want_key))})"
        )
    return "; ".join(parts) or None
