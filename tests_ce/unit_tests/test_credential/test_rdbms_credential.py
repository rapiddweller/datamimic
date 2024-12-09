# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/
from copy import copy

from datamimic_ce.credentials.rdbms_credential import RdbmsCredential
from datamimic_ce.model.database_model import DatabaseModel


class TestRdbmsCredential:

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

    def test_get_credentials(self):
        for _ in range(100):
            rdbms_credential = RdbmsCredential(**self.database_model.model_dump())
            temp_credentials = rdbms_credential.get_credentials()
            assert self.database_model.dbms == temp_credentials["dbms"]
            assert self.database_model.host == temp_credentials["host"]
            assert self.database_model.port == str(temp_credentials["port"])
            assert self.database_model.user == temp_credentials["user"]
            assert self.database_model.password == temp_credentials["password"]
            assert self.database_model.database == temp_credentials["database"]
            assert self.database_model.db_schema == temp_credentials["db_schema"]

    def test_check_credentials(self):
        for _ in range(100):
            rdbms_credential = RdbmsCredential(**self.database_model.model_dump())
            try:
                assert rdbms_credential.check_credentials()
            except ValueError:
                assert False

    def test_check_credentials_no_dbms(self):
        rdbms_model = copy(self.database_model)
        rdbms_model.dbms = ""
        for _ in range(100):
            rdbms_credential = RdbmsCredential(**rdbms_model.model_dump())
            try:
                rdbms_credential.check_credentials()
                assert False
            except ValueError as error:
                assert str(error) == "DBMS is required"

    def test_check_credentials_no_host(self):
        rdbms_model = copy(self.database_model)
        rdbms_model.host = ""
        for _ in range(100):
            rdbms_credential = RdbmsCredential(**rdbms_model.model_dump())
            try:
                rdbms_credential.check_credentials()
                assert False
            except ValueError as error:
                assert str(error) == "Host is required"

    def test_check_credentials_no_port(self):
        rdbms_model = copy(self.database_model)
        rdbms_model.port = 0
        for _ in range(100):
            rdbms_credential = RdbmsCredential(**rdbms_model.model_dump())
            try:
                rdbms_credential.check_credentials()
                assert False
            except ValueError as error:
                assert str(error) == "Port is required"

    def test_check_credentials_no_database(self):
        rdbms_model = copy(self.database_model)
        rdbms_model.database = ""
        for _ in range(100):
            rdbms_credential = RdbmsCredential(**rdbms_model.model_dump())
            try:
                rdbms_credential.check_credentials()
                assert False
            except ValueError as error:
                assert str(error) == "Database is required"

    def test_check_credentials_no_user(self):
        rdbms_model = copy(self.database_model)
        rdbms_model.user = ""
        for _ in range(100):
            rdbms_credential = RdbmsCredential(**rdbms_model.model_dump())
            try:
                rdbms_credential.check_credentials()
                assert False
            except ValueError as error:
                assert str(error) == "User is required"

    def test_check_credentials_no_password(self):
        rdbms_model = copy(self.database_model)
        rdbms_model.password = ""
        for _ in range(100):
            rdbms_credential = RdbmsCredential(**rdbms_model.model_dump())
            try:
                rdbms_credential.check_credentials()
                assert False
            except ValueError as error:
                assert str(error) == "Password is required"

    def test_check_credentials_no_schema(self):
        rdbms_model = copy(self.database_model)
        rdbms_model.db_schema = None
        for _ in range(100):
            rdbms_credential = RdbmsCredential(**rdbms_model.model_dump())
            try:
                rdbms_credential.check_credentials()
                assert False
            except ValueError as error:
                assert str(error) == "DB Schema is required"
