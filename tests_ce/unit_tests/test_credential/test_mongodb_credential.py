# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
from copy import copy

from datamimic_ce.credentials.mongodb_credential import MongoDBCredential
from datamimic_ce.model.mongodb_model import MongoDBModel


class TestMongodbCredential:
    mongodb_model = MongoDBModel(
        id="mongodb",
        host="localhost",
        port="47017",
        database="datamimic",
        user="datamimic",
        password="datamimic",
        environment=None,
    )

    def test_get_credentials(self):
        for _ in range(100):
            mongodb_credential = MongoDBCredential(**self.mongodb_model.model_dump())
            temp_credentials = mongodb_credential.get_credentials()
            assert self.mongodb_model.host == temp_credentials["host"]
            assert self.mongodb_model.port == str(temp_credentials["port"])
            assert self.mongodb_model.database == temp_credentials["database"]
            assert self.mongodb_model.user == temp_credentials["user"]
            assert self.mongodb_model.password == temp_credentials["password"]

    def test_check_credentials(self):
        for _ in range(100):
            mongodb_credential = MongoDBCredential(**self.mongodb_model.model_dump())
            try:
                assert mongodb_credential.check_credentials()
            except ValueError:
                assert False

    def test_check_credentials_no_host(self):
        mongodb_model = copy(self.mongodb_model)
        mongodb_model.host = ""
        for _ in range(100):
            mongodb_credential = MongoDBCredential(**mongodb_model.model_dump())
            try:
                mongodb_credential.check_credentials()
                assert False
            except ValueError as error:
                assert str(error) == "Host is required"

    def test_check_credentials_no_port(self):
        mongodb_model = copy(self.mongodb_model)
        mongodb_model.port = 0
        for _ in range(100):
            mongodb_credential = MongoDBCredential(**mongodb_model.model_dump())
            try:
                mongodb_credential.check_credentials()
                assert False
            except ValueError as error:
                assert str(error) == "Port is required"

    def test_check_credentials_no_database(self):
        mongodb_model = copy(self.mongodb_model)
        mongodb_model.database = ""
        for _ in range(100):
            mongodb_credential = MongoDBCredential(**mongodb_model.model_dump())
            try:
                mongodb_credential.check_credentials()
                assert False
            except ValueError as error:
                assert str(error) == "Database is required"

    def test_check_credentials_no_user(self):
        mongodb_model = copy(self.mongodb_model)
        mongodb_model.user = ""
        for _ in range(100):
            mongodb_credential = MongoDBCredential(**mongodb_model.model_dump())
            try:
                mongodb_credential.check_credentials()
                assert False
            except ValueError as error:
                assert str(error) == "User is required"

    def test_check_credentials_no_password(self):
        mongodb_model = copy(self.mongodb_model)
        mongodb_model.password = ""
        for _ in range(100):
            mongodb_credential = MongoDBCredential(**mongodb_model.model_dump())
            try:
                mongodb_credential.check_credentials()
                assert False
            except ValueError as error:
                assert str(error) == "Password is required"
