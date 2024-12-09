# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/



from pathlib import Path

from bson import ObjectId

from datamimic_ce.data_mimic_test import DataMimicTest


class TestMongoDbErrorFunction:
    _test_dir = Path(__file__).resolve().parent

    def test_mongodb_missing_selector_and_type(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_mongodb_missing_selector_and_type.xml")
        try:
            engine.test_with_timer()
            assert False
        except ValueError as err:
            assert str(err) == "MongoDB source requires at least attribute 'type', 'selector' or 'iterationSelector'"

    def test_mongodb_wrong_query_type(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_mongodb_wrong_query_type.xml")
        try:
            engine.test_with_timer()
            assert False
        except ValueError as err:
            assert str(err) == ("Error while executing query 'update: 'mongo_func_test', filter: {}', "
                                "currently Mongodb selector only support 'find' and 'aggregate'")

    def test_mongodb_two_find_query(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_mongodb_two_find_query.xml")
        try:
            engine.test_with_timer()
            assert False
        except ValueError as err:
            assert str(err) == "Error syntax, only 1 'find' allow but found 2"

    def test_mongodb_two_aggregate_query(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_mongodb_two_aggregate_query.xml")
        try:
            engine.test_with_timer()
            assert False
        except ValueError as err:
            assert str(err) == "Error syntax, only 1 'aggregate' allow but found 2"

    def test_mongodb_find_and_aggregate_error(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_mongodb_find_and_aggregate_error.xml")
        try:
            engine.test_with_timer()
            assert False
        except ValueError as err:
            assert str(err) == "Error syntax, only one query type allow but found both 'find' and 'aggregate'"

    def test_mongodb_two_filter(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_mongodb_two_filter.xml")
        try:
            engine.test_with_timer()
            assert False
        except ValueError as err:
            assert str(err) == "Error syntax, only 1 'filter' allow but found 2"

    def test_mongodb_two_projection(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_mongodb_two_projection.xml")
        try:
            engine.test_with_timer()
            assert False
        except ValueError as err:
            assert str(err) == "Error syntax, only 1 'projection' allow but found 2"

    def test_mongodb_two_pipeline(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_mongodb_two_pipeline.xml")
        try:
            engine.test_with_timer()
            assert False
        except ValueError as err:
            assert str(err) == "Error syntax, only 1 'pipeline' allow but found 2"

    def test_mongodb_pipeline_syntax_error(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_mongodb_pipeline_syntax_error.xml")
        try:
            engine.test_with_timer()
            assert False
        except ValueError as err:
            assert str(err) == "Syntax error: pipeline value must be a list"

    def test_mongodb_pipeline_not_exist(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_mongodb_pipeline_not_exist.xml")
        try:
            engine.test_with_timer()
            assert False
        except ValueError as err:
            assert str(err) == ("Wrong mongodb selector syntax: aggregate: 'mongo_func_test', "
                                "error: Wrong query syntax 'pipeline' component not found")

    def test_mongodb_filter_not_exist(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_mongodb_filter_not_exist.xml")
        try:
            engine.test_with_timer()
            assert False
        except ValueError as err:
            assert str(err) == ("Wrong mongodb selector syntax: find: 'mongo_func_test', "
                                "error: Wrong query syntax 'filter' component not found")
