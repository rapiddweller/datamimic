# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

from bson import ObjectId

from datamimic_ce.data_mimic_test import DataMimicTest
import pytest


class TestMongoDbErrorFunction:
    _test_dir = Path(__file__).resolve().parent

    @pytest.mark.asyncio
    async def test_mongodb_missing_selector_and_type(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_mongodb_missing_selector_and_type.xml")
        try:
            await test_engine.test_with_timer()
            assert False
        except ValueError as err:
            assert str(err) == "MongoDB source requires at least attribute 'type', 'selector' or 'iterationSelector'"

    @pytest.mark.asyncio
    async def test_mongodb_wrong_query_type(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_mongodb_wrong_query_type.xml")
        try:
            await test_engine.test_with_timer()
            assert False
        except ValueError as err:
            assert str(err) == (
                "Error while executing query 'update: 'mongo_func_test', filter: {}', "
                "currently Mongodb selector only support 'find' and 'aggregate'"
            )

    @pytest.mark.asyncio
    async def test_mongodb_two_find_query(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_mongodb_two_find_query.xml")
        try:
            await test_engine.test_with_timer()
            assert False
        except ValueError as err:
            assert str(err) == "Error syntax, only 1 'find' allow but found 2"

    @pytest.mark.asyncio
    async def test_mongodb_two_aggregate_query(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_mongodb_two_aggregate_query.xml")
        try:
            await test_engine.test_with_timer()
            assert False
        except ValueError as err:
            assert str(err) == "Error syntax, only 1 'aggregate' allow but found 2"

    @pytest.mark.asyncio
    async def test_mongodb_find_and_aggregate_error(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_mongodb_find_and_aggregate_error.xml")
        try:
            await test_engine.test_with_timer()
            assert False
        except ValueError as err:
            assert str(err) == "Error syntax, only one query type allow but found both 'find' and 'aggregate'"

    @pytest.mark.asyncio
    async def test_mongodb_two_filter(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_mongodb_two_filter.xml")
        try:
            await test_engine.test_with_timer()
            assert False
        except ValueError as err:
            assert str(err) == "Error syntax, only 1 'filter' allow but found 2"

    @pytest.mark.asyncio
    async def test_mongodb_two_projection(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_mongodb_two_projection.xml")
        try:
            await test_engine.test_with_timer()
            assert False
        except ValueError as err:
            assert str(err) == "Error syntax, only 1 'projection' allow but found 2"

    @pytest.mark.asyncio
    async def test_mongodb_two_pipeline(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_mongodb_two_pipeline.xml")
        try:
            await test_engine.test_with_timer()
            assert False
        except ValueError as err:
            assert str(err) == "Error syntax, only 1 'pipeline' allow but found 2"

    @pytest.mark.asyncio
    async def test_mongodb_pipeline_syntax_error(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_mongodb_pipeline_syntax_error.xml")
        try:
            await test_engine.test_with_timer()
            assert False
        except ValueError as err:
            assert str(err) == "Syntax error: pipeline value must be a list"

    @pytest.mark.asyncio
    async def test_mongodb_pipeline_not_exist(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_mongodb_pipeline_not_exist.xml")
        try:
            await test_engine.test_with_timer()
            assert False
        except ValueError as err:
            assert str(err) == (
                "Wrong mongodb selector syntax: aggregate: 'mongo_func_test', "
                "error: Wrong query syntax 'pipeline' component not found"
            )

    @pytest.mark.asyncio
    async def test_mongodb_filter_not_exist(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_mongodb_filter_not_exist.xml")
        try:
            await test_engine.test_with_timer()
            assert False
        except ValueError as err:
            assert str(err) == (
                "Wrong mongodb selector syntax: find: 'mongo_func_test', "
                "error: Wrong query syntax 'filter' component not found"
            )
