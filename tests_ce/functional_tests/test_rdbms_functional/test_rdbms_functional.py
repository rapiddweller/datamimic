# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from datetime import datetime
from pathlib import Path

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest
import pytest


class TestRdbmsFunctional:
    _test_dir = Path(__file__).resolve().parent

    @pytest.mark.skip(reason="MSSQL on testing server is not available Apr 8 2024")
    async def test_mssql_functional(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="more_mssql_test.xml", capture_test_result=True)
        await test_engine.test_with_timer()
        result = test_engine.capture_result()
        assert len(result) == 8

        simple_user = result["simple_user"]
        assert len(simple_user) == 10

        in_out = result["in_out"]
        assert len(in_out) == 10

        iterate_simple_user = result["iterate_simple_user"]
        assert iterate_simple_user == simple_user

        self._assert_iterate(result, True)

        cross_collection = result["cross_collection"]
        assert len(cross_collection) == 10

    @pytest.mark.skip(reason="This test should be move to another job or only run on local machine")
    async def test_mysql_functional(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="more_mysql_test.xml", capture_test_result=True)
        await test_engine.test_with_timer()
        result = test_engine.capture_result()
        assert len(result) == 8

        simple_user = result["simple_user"]
        assert len(simple_user) == 10

        in_out = result["in_out"]
        assert len(in_out) == 10

        iterate_simple_user = result["iterate_simple_user"]
        assert iterate_simple_user == simple_user

        self._assert_iterate(result, False)

        cross_collection = result["cross_collection"]
        assert len(cross_collection) == 10

    @pytest.mark.asyncio
    async def test_postgres_functional(self):
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="more_postgresql_test.xml", capture_test_result=True
        )
        await test_engine.test_with_timer()
        result = test_engine.capture_result()
        assert len(result) == 8

        simple_user = result["simple_user"]
        assert len(simple_user) == 10

        in_out = result["in_out"]
        assert len(in_out) == 10

        iterate_simple_user = result["iterate_simple_user"]
        assert iterate_simple_user == simple_user

        self._assert_iterate(result, True)

        cross_collection = result["cross_collection"]
        assert len(cross_collection) == 10

    @pytest.mark.skip(reason="This test should be move to another job")
    async def test_oracle_functional(self):
        try:
            test_engine = DataMimicTest(
                test_dir=self._test_dir, filename="more_oracle_test.xml", capture_test_result=True
            )
            await test_engine.test_with_timer()
            result = test_engine.capture_result()
        except Exception as e:
            # TODO: Create mock service for Oracle
            pytest.skip(f"Skipping test due to Oracle connection error: {e}")

        # Verify the length of the result
        assert len(result) == 8, f"Expected result length 8, got {len(result)}"

        # Verify SIMPLE_USER
        simple_user = result["SIMPLE_USER"]
        assert len(simple_user) == 10, f"Expected SIMPLE_USER length 10, got {len(simple_user)}"

        # Verify in_out
        in_out = result["in_out"]
        assert len(in_out) == 10, f"Expected in_out length 10, got {len(in_out)}"

        # Verify iterate_simple_user
        iterate_simple_user = result["iterate_simple_user"]
        assert len(iterate_simple_user) == len(
            simple_user
        ), f"Expected iterate_simple_user length {len(simple_user)}, got {len(iterate_simple_user)}"
        for i in range(len(simple_user)):
            for key, value in simple_user[i].items():
                assert iterate_simple_user[i].get(key) == value, (
                    f"Mismatch at index {i} for key '{key}': "
                    f"expected {value}, got {iterate_simple_user[i].get(key)}"
                )

        self._assert_iterate(result, False)

        # Verify cross_collection
        cross_collection = result["cross_collection"]
        assert len(cross_collection) == 10, f"Expected cross_collection length 10, got {len(cross_collection)}"

    @staticmethod
    def _assert_iterate(result, have_bool: bool):
        iterate_customer = result["iterate_customer"]
        assert len(iterate_customer) == 10
        count = 1
        for customer in iterate_customer:
            assert customer.get("id") == count
            assert customer.get("tc_creation_src") == "BEN"
            assert isinstance(customer.get("tc_creation"), datetime)
            assert customer.get("no") == f"{count}"
            if have_bool:
                assert isinstance(customer.get("active"), bool)
                assert customer.get("active") is False
            else:
                assert customer.get("active") in [0, 1]
            assert isinstance(customer.get("name"), str)
            count += 1

        iterate_user = result["iterate_user"]
        assert len(iterate_user) == 10
        count = 1
        for user in iterate_user:
            assert user.get("id") == count
            assert user.get("tc_creation_src") == "BEN"
            assert isinstance(user.get("tc_creation"), datetime)
            assert isinstance(user.get("full_name"), str)
            assert user.get("email") == f"{user.get('id')}"
            if have_bool:
                assert isinstance(user.get("active"), bool)
                assert isinstance(user.get("superuser"), bool)
            else:
                assert user.get("active") in [0, 1]
                assert user.get("superuser") in [0, 1]
            assert isinstance(user.get("hashed_password"), str)
            assert user.get("language") in ["german", "english", "vietnamese"]
            assert any(customer.get("id") == user.get("customer_id") for customer in iterate_customer)
            count += 1
