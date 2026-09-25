# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
from copy import copy

import pytest
from pydantic import ValidationError

from datamimic_ce.engine.dsl.model.database_model import DatabaseModel
from datamimic_ce.engine.io.connection_config.rdbms_connection_config import RdbmsConnectionConfig


class TestRdbmsConnectionConfig:
    database_model = DatabaseModel(
        id="sourceDB",
        host="localhost",
        port="45432",
        database="rd-datamimic",
        dbms="postgresql",
        schema="simple",
        user="rdadm",
        password="rdtest!",
        environment=None,
    )

    def test_get_connection_config(self):
        for _ in range(100):
            rdbms_config = RdbmsConnectionConfig(**self.database_model.model_dump())
            temp_config = rdbms_config.get_connection_config()
            assert self.database_model.dbms == temp_config["dbms"]
            assert self.database_model.host == temp_config["host"]
            assert self.database_model.port == str(temp_config["port"])
            assert self.database_model.user == temp_config["user"]
            assert self.database_model.password == temp_config["password"]
            assert self.database_model.database == temp_config["database"]
            assert self.database_model.db_schema == temp_config["db_schema"]

    def test_check_connection_config(self):
        for _ in range(100):
            rdbms_config = RdbmsConnectionConfig(**self.database_model.model_dump())
            try:
                assert rdbms_config.check_connection_config()
            except ValueError:
                assert False

    @pytest.mark.parametrize("dbms", ["", "postgres", "db2"])
    def test_unsupported_dbms_is_rejected_when_the_config_is_built(self, dbms):
        with pytest.raises(ValidationError, match="dbms"):
            RdbmsConnectionConfig(**{**self.database_model.model_dump(), "dbms": dbms})

    def test_check_connection_config_no_host(self):
        rdbms_model = copy(self.database_model)
        rdbms_model.host = ""
        for _ in range(100):
            rdbms_config = RdbmsConnectionConfig(**rdbms_model.model_dump())
            try:
                rdbms_config.check_connection_config()
                assert False
            except ValueError as error:
                assert str(error) == "Host is required"

    def test_check_connection_config_no_port(self):
        rdbms_model = copy(self.database_model)
        rdbms_model.port = 0
        for _ in range(100):
            rdbms_config = RdbmsConnectionConfig(**rdbms_model.model_dump())
            try:
                rdbms_config.check_connection_config()
                assert False
            except ValueError as error:
                assert str(error) == "Port is required"

    def test_check_connection_config_no_database(self):
        rdbms_model = copy(self.database_model)
        rdbms_model.database = ""
        for _ in range(100):
            rdbms_config = RdbmsConnectionConfig(**rdbms_model.model_dump())
            try:
                rdbms_config.check_connection_config()
                assert False
            except ValueError as error:
                assert str(error) == "Database is required"

    def test_check_connection_config_no_user(self):
        rdbms_model = copy(self.database_model)
        rdbms_model.user = ""
        for _ in range(100):
            rdbms_config = RdbmsConnectionConfig(**rdbms_model.model_dump())
            try:
                rdbms_config.check_connection_config()
                assert False
            except ValueError as error:
                assert str(error) == "User is required"

    def test_check_connection_config_no_password(self):
        rdbms_model = copy(self.database_model)
        rdbms_model.password = ""
        for _ in range(100):
            rdbms_config = RdbmsConnectionConfig(**rdbms_model.model_dump())
            try:
                rdbms_config.check_connection_config()
                assert False
            except ValueError as error:
                assert str(error) == "Password is required"

    def test_check_connection_config_no_schema(self):
        rdbms_model = copy(self.database_model)
        rdbms_model.db_schema = None
        for _ in range(100):
            rdbms_config = RdbmsConnectionConfig(**rdbms_model.model_dump())
            try:
                rdbms_config.check_connection_config()
                assert False
            except ValueError as error:
                assert str(error) == "DB Schema is required"
