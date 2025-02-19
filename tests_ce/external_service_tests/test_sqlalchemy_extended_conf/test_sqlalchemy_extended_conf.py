# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
import os
from pathlib import Path

import sqlalchemy

from datamimic_ce.data_mimic_test import DataMimicTest
from datamimic_ce.utils.file_util import FileUtil


class TestSqlAlchemyExtendedConf:
    _test_dir = Path(__file__).resolve().parent

    def test_none_as_null(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_none_as_null.xml")
        test_engine.test_with_timer()

        env_file = f"conf/{'local' if os.getenv('RUNTIME_ENVIRONMENT') == 'development' else 'environment'}.env.properties"
        conf_dict = FileUtil.parse_properties(self._test_dir / env_file)
        host = conf_dict["postgres.db.host"]
        port = conf_dict["postgres.db.port"]
        user = conf_dict["postgres.db.user"]
        password = conf_dict["postgres.db.password"]
        database = conf_dict["postgres.db.database"]
        schema = conf_dict["postgres.db.schema"]
        sqlalchemy_engine = sqlalchemy.create_engine(
            "postgresql+psycopg2://{}:{}@{}:{}/{}".format(user, password, host, port, database))
        connection = sqlalchemy_engine.connect()
        # Fetch all records
        all_records = connection.execute(sqlalchemy.text(f"SELECT * FROM {schema}.none_as_null")).fetchall()
        # Fetch records where data_null is SQL null
        data_null = connection.execute(
            sqlalchemy.text(f"SELECT * FROM {schema}.none_as_null WHERE data_null IS NULL")).fetchall()
        # Fetch records where data_none is SQL null (0 records)
        false_data_none = connection.execute(
            sqlalchemy.text(f"SELECT * FROM {schema}.none_as_null WHERE data_none IS NULL")).fetchall()
        # Fetch records where data_none is 'null' (5 records)
        true_data_none = connection.execute(
            sqlalchemy.text(f"SELECT * FROM {schema}.none_as_null WHERE data_none = 'null'")).fetchall()
        
        assert len(all_records) == 5
        assert len(data_null) == 5
        assert len(false_data_none) == 0
        assert len(true_data_none) == 5
