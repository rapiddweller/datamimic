# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
from copy import copy

from datamimic_ce.connection_config.mongodb_connection_config import MongoDBConnectionConfig
from datamimic_ce.model.mongodb_model import MongoDBModel


class TestMongodbConnectionConfig:
    mongodb_model = MongoDBModel(
        id="mongodb",
        host="localhost",
        port="47017",
        database="datamimic",
        user="datamimic",
        password="datamimic",
        environment=None,
    )

    def test_get_connection_config(self):
        for _ in range(100):
            mongodb_config = MongoDBConnectionConfig(**self.mongodb_model.model_dump())
            temp_config = mongodb_config.get_connection_config()
            assert self.mongodb_model.host == temp_config["host"]
            assert self.mongodb_model.port == str(temp_config["port"])
            assert self.mongodb_model.database == temp_config["database"]
            assert self.mongodb_model.user == temp_config["user"]
            assert self.mongodb_model.password == temp_config["password"]

    def test_check_connection_config(self):
        for _ in range(100):
            mongodb_config = MongoDBConnectionConfig(**self.mongodb_model.model_dump())
            try:
                assert mongodb_config.check_connection_config()
            except ValueError:
                assert False

    def test_check_connection_config_no_host(self):
        mongodb_model = copy(self.mongodb_model)
        mongodb_model.host = ""
        for _ in range(100):
            mongodb_config = MongoDBConnectionConfig(**mongodb_model.model_dump())
            try:
                mongodb_config.check_connection_config()
                assert False
            except ValueError as error:
                assert str(error) == "Host is required"

    def test_check_connection_config_no_port(self):
        mongodb_model = copy(self.mongodb_model)
        mongodb_model.port = 0
        for _ in range(100):
            mongodb_config = MongoDBConnectionConfig(**mongodb_model.model_dump())
            try:
                mongodb_config.check_connection_config()
                assert False
            except ValueError as error:
                assert str(error) == "Port is required"

    def test_check_connection_config_no_database(self):
        mongodb_model = copy(self.mongodb_model)
        mongodb_model.database = ""
        for _ in range(100):
            mongodb_config = MongoDBConnectionConfig(**mongodb_model.model_dump())
            try:
                mongodb_config.check_connection_config()
                assert False
            except ValueError as error:
                assert str(error) == "Database is required"

    def test_check_connection_config_no_user(self):
        mongodb_model = copy(self.mongodb_model)
        mongodb_model.user = ""
        for _ in range(100):
            mongodb_config = MongoDBConnectionConfig(**mongodb_model.model_dump())
            try:
                mongodb_config.check_connection_config()
                assert False
            except ValueError as error:
                assert str(error) == "User is required"

    def test_check_connection_config_no_password(self):
        mongodb_model = copy(self.mongodb_model)
        mongodb_model.password = ""
        for _ in range(100):
            mongodb_config = MongoDBConnectionConfig(**mongodb_model.model_dump())
            try:
                mongodb_config.check_connection_config()
                assert False
            except ValueError as error:
                assert str(error) == "Password is required"
