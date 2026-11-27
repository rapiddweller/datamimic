# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""RdbmsClient._create_engine's MSSQL dialect selection: driver="pymssql" (the pure-Python
FreeTDS opt-in, no proprietary ODBC package needed) vs. the default ODBC Driver 17 path.
Mocks sqlalchemy.create_engine itself - no real connection needed to verify which dialect
string/URL gets built for which credential."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.engine import make_url

from datamimic_ce.engine.io.clients.rdbms_client import RdbmsClient
from datamimic_ce.engine.io.connection_config.rdbms_connection_config import RdbmsConnectionConfig
from datamimic_ce.engine.runtime.lifecycle.config import get_settings
from datamimic_ce.errors import ClientConfigError, IssueCode


def _credential(**extra) -> RdbmsConnectionConfig:
    return RdbmsConnectionConfig(
        dbms="mssql",
        host="localhost",
        port=1433,
        user="sa",
        password="pw",
        database="master",
        db_schema="dbo",
        **extra,
    )


class TestRdbmsClientMssqlEngineSelection:
    def test_default_uses_pyodbc(self):
        client = RdbmsClient(credential=_credential())
        with patch(
            "datamimic_ce.engine.io.clients.rdbms_client.sqlalchemy.create_engine", return_value=MagicMock()
        ) as mock_ce:
            client._create_engine()
        url = mock_ce.call_args[0][0]
        assert url.startswith("mssql+pyodbc://")
        assert "driver=ODBC+Driver+17+for+SQL+Server" in url

    def test_driver_pymssql_opts_into_pure_python_driver(self):
        client = RdbmsClient(credential=_credential(driver="pymssql"))
        with patch(
            "datamimic_ce.engine.io.clients.rdbms_client.sqlalchemy.create_engine", return_value=MagicMock()
        ) as mock_ce:
            client._create_engine()
        url = mock_ce.call_args[0][0]
        assert url.startswith("mssql+pymssql://")

    def test_unrecognized_driver_value_falls_back_to_pyodbc(self):
        """Only the literal 'pymssql' opts in; a typo falls back to the documented default."""
        client = RdbmsClient(credential=_credential(driver="freetds"))
        with patch(
            "datamimic_ce.engine.io.clients.rdbms_client.sqlalchemy.create_engine", return_value=MagicMock()
        ) as mock_ce:
            client._create_engine()
        url = mock_ce.call_args[0][0]
        assert url.startswith("mssql+pyodbc://")


@pytest.mark.parametrize("environment", ["development", "production"])
def test_sqlite_uses_task_directory_in_each_supported_environment(tmp_path, monkeypatch, environment):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(get_settings(), "RUNTIME_ENVIRONMENT", environment)
    credential = RdbmsConnectionConfig(
        dbms="sqlite",
        host=None,
        port=None,
        user=None,
        password=None,
        database="warehouse",
        db_schema=None,
    )
    client = RdbmsClient(credential=credential, task_id="run-1")

    with patch(
        "datamimic_ce.engine.io.clients.rdbms_client.sqlalchemy.create_engine", return_value=MagicMock()
    ) as create:
        client._create_engine()

    assert create.call_args.args[0] == f"sqlite:///{Path('db') / 'warehouse.sqlite'}"
    assert (tmp_path / "db").is_dir()


def test_sqlite_requires_task_id(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    credential = RdbmsConnectionConfig(
        dbms="sqlite",
        host=None,
        port=None,
        user=None,
        password=None,
        database="warehouse",
        db_schema=None,
    )
    client = RdbmsClient(credential=credential)

    with pytest.raises(ValueError, match="Task ID is required to create SQLite db in task folder"):
        client._create_engine()


def _oracle_credential(**extra) -> RdbmsConnectionConfig:
    return RdbmsConnectionConfig(
        dbms="oracle",
        host="db.example",
        port=1521,
        user="rdadm",
        password="p@ss",
        database="rddb",
        db_schema="RDADM",
        **extra,
    )


class TestRdbmsClientOracleEngineSelection:
    def test_url_selects_the_oracledb_dialect_with_service_name(self):
        client = RdbmsClient(credential=_oracle_credential())
        with patch(
            "datamimic_ce.engine.io.clients.rdbms_client.sqlalchemy.create_engine", return_value=MagicMock()
        ) as mock_ce:
            client._create_engine()
        url = mock_ce.call_args[0][0]
        assert url == "oracle+oracledb://rdadm:p%40ss@db.example:1521/?service_name=rddb"
        parsed = make_url(url)
        assert (parsed.get_backend_name(), parsed.get_driver_name()) == ("oracle", "oracledb")
        assert parsed.get_dialect().__name__ == "OracleDialect_oracledb"

    def test_selection_does_not_write_to_the_import_table(self, monkeypatch):
        monkeypatch.delitem(sys.modules, "cx_Oracle", raising=False)
        before = dict(sys.modules)
        client = RdbmsClient(credential=_oracle_credential())
        with patch("datamimic_ce.engine.io.clients.rdbms_client.sqlalchemy.create_engine", return_value=MagicMock()):
            client._create_engine()
        assert "cx_Oracle" not in sys.modules
        assert sys.modules == before

    def test_missing_driver_is_a_typed_client_configuration_error(self, monkeypatch):
        monkeypatch.setitem(sys.modules, "oracledb", None)  # the import fails as if the package were absent
        monkeypatch.delitem(sys.modules, "cx_Oracle", raising=False)
        client = RdbmsClient(credential=_oracle_credential())

        with pytest.raises(ClientConfigError) as raised:
            client._create_engine()

        assert raised.value.issue_code is IssueCode.CLIENT_PREFLIGHT_INVALID_CONFIGURATION
        assert "python-oracledb driver is not installed" in str(raised.value)
        assert isinstance(raised.value.__cause__, ImportError)
        assert client.engine is None
        assert "cx_Oracle" not in sys.modules

    @pytest.mark.parametrize(
        ("dbms", "port", "scheme"),
        [("postgresql", 5432, "postgresql+psycopg2"), ("mysql", 3306, "mysql+mysqlconnector")],
    )
    def test_other_dialects_keep_their_driver_urls(self, dbms, port, scheme):
        credential = RdbmsConnectionConfig(
            dbms=dbms, host="h", port=port, user="u", password="pw", database="d", db_schema=None
        )
        with patch(
            "datamimic_ce.engine.io.clients.rdbms_client.sqlalchemy.create_engine", return_value=MagicMock()
        ) as mock_ce:
            RdbmsClient(credential=credential)._create_engine()
        assert mock_ce.call_args[0][0] == f"{scheme}://u:pw@h:{port}/d"
