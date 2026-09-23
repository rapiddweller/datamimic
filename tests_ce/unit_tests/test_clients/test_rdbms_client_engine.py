# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""RdbmsClient._create_engine's MSSQL dialect selection: driver="pymssql" (the pure-Python
FreeTDS opt-in, no proprietary ODBC package needed) vs. the default ODBC Driver 17 path.
Mocks sqlalchemy.create_engine itself - no real connection needed to verify which dialect
string/URL gets built for which credential."""

from unittest.mock import MagicMock, patch

import pytest

from datamimic_ce.engine.io.clients.rdbms_client import RdbmsClient
from datamimic_ce.engine.io.connection_config.rdbms_connection_config import RdbmsConnectionConfig
from datamimic_ce.engine.runtime.config import settings


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
    monkeypatch.setattr(settings, "RUNTIME_ENVIRONMENT", environment)
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

    assert create.call_args.args[0] == "sqlite:///db/warehouse.sqlite"
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
