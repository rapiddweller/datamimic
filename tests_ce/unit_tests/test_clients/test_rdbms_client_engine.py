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

from datamimic_ce.clients.rdbms_client import RdbmsClient
from datamimic_ce.connection_config.rdbms_connection_config import RdbmsConnectionConfig


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
        with patch("datamimic_ce.clients.rdbms_client.sqlalchemy.create_engine", return_value=MagicMock()) as mock_ce:
            client._create_engine()
        url = mock_ce.call_args[0][0]
        assert url.startswith("mssql+pyodbc://")
        assert "driver=ODBC+Driver+17+for+SQL+Server" in url

    def test_driver_pymssql_opts_into_pure_python_driver(self):
        client = RdbmsClient(credential=_credential(driver="pymssql"))
        with patch("datamimic_ce.clients.rdbms_client.sqlalchemy.create_engine", return_value=MagicMock()) as mock_ce:
            client._create_engine()
        url = mock_ce.call_args[0][0]
        assert url.startswith("mssql+pymssql://")

    def test_unrecognized_driver_value_falls_back_to_pyodbc(self):
        """Only the literal 'pymssql' opts in - any other/typo'd value falls back to the
        documented default rather than silently misrouting."""
        client = RdbmsClient(credential=_credential(driver="freetds"))
        with patch("datamimic_ce.clients.rdbms_client.sqlalchemy.create_engine", return_value=MagicMock()) as mock_ce:
            client._create_engine()
        url = mock_ce.call_args[0][0]
        assert url.startswith("mssql+pyodbc://")
