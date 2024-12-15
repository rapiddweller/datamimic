# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

from bson import ObjectId

from datamimic_ce.data_mimic_test import DataMimicTest
import pytest


class TestMongoDbFunction:
    _test_dir = Path(__file__).resolve().parent

    @pytest.mark.asyncio
    async def test_mongodb_consumer(self):
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_mongodb_consumer.xml", capture_test_result=True
        )
        await test_engine.test_with_timer()

        result = test_engine.capture_result()
        mongo_data = result["mongo_func_test"]
        query_check = result["query_check"]
        selector_check = result["selector_check"]
        update_check = result["update_check"]
        upsert_check = result["upsert_check"]
        delete_check = result["delete_check"]

        assert len(query_check) == 150
        assert all(query_row["name"] in ["Bob", "Frank", "Phil"] for query_row in query_check)

        bob_count = 0
        for db in mongo_data:
            if db["user_name"] == "Bob":
                bob_count += 1

        assert len(selector_check) == len(mongo_data) - bob_count
        assert all(selector_row["user_name"] in ["Frank", "Phil"] for selector_row in selector_check)
        assert all(selector_row["user_name"] != "Bob" for selector_row in selector_check)

        assert len(update_check) == 150
        assert all(update_row["addition"] in ["Addition 1", "Addition 2", "Addition 3"] for update_row in update_check)

        insert_mary = 0 if any(db["user_name"] == "Mary" for db in mongo_data) else 1
        assert len(upsert_check) == len(mongo_data) + insert_mary
        assert any(upsert_row["user_name"] == "Mary" for upsert_row in upsert_check)
        for upsert_row in upsert_check:
            if upsert_row["user_name"] == "Mary":
                assert upsert_row["addition"] in ["addition_value1", "addition_value2", "addition_value3"]
                assert upsert_row["second_addition"] in ["value1", "value2", "value3"]
                assert upsert_row["other_addition"] in ["other_value1", "other_value2", "other_value3"]

        assert len(delete_check) == bob_count

    @pytest.mark.asyncio
    async def test_mongodb_cross_collection(self):
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_mongodb_cross_collection.xml", capture_test_result=True
        )
        await test_engine.test_with_timer()

        result = test_engine.capture_result()
        summary_datas = result["summary"]
        assert len(summary_datas) == 10
        assert set([d["users_orders"]["_id"] for d in summary_datas]) == set(range(1, 11))
        for data in summary_datas:
            user_id = data["users_orders"]["_id"]
            user_orders = data["users_orders"]["orders"]
            assert len(user_orders) == 1
            user_order = user_orders[0]
            if user_id == 1:
                assert user_order["user_id"] == 1
                assert user_order["order_item"] == "notebook"
                assert user_order["quantity"] == 7
            elif user_id == 2:
                assert user_order["user_id"] == 2
                assert user_order["order_item"] == "book"
                assert user_order["quantity"] == 7
            elif user_id == 3:
                assert user_order["user_id"] == 3
                assert user_order["order_item"] == "pencil"
                assert user_order["quantity"] == 10
            elif user_id == 4:
                assert user_order["user_id"] == 4
                assert user_order["order_item"] == "book"
                assert user_order["quantity"] == 10
            elif user_id == 5:
                assert user_order["user_id"] == 5
                assert user_order["order_item"] == "book"
                assert user_order["quantity"] == 10
            elif user_id == 6:
                assert user_order["user_id"] == 6
                assert user_order["order_item"] == "notebook"
                assert user_order["quantity"] == 7
            elif user_id == 7:
                assert user_order["user_id"] == 7
                assert user_order["order_item"] == "pencil"
                assert user_order["quantity"] == 7
            elif user_id == 8:
                assert user_order["user_id"] == 8
                assert user_order["order_item"] == "book"
                assert user_order["quantity"] == 5
            elif user_id == 9:
                assert user_order["user_id"] == 9
                assert user_order["order_item"] == "notebook"
                assert user_order["quantity"] == 10
            elif user_id == 10:
                assert user_order["user_id"] == 10
                assert user_order["order_item"] == "pencil"
                assert user_order["quantity"] == 10

    @pytest.mark.asyncio
    async def test_mongodb_more_cross_collection(self):
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_mongodb_more_cross_collection.xml", capture_test_result=True
        )
        await test_engine.test_with_timer()

        result = test_engine.capture_result()
        summary = result["more_summary"]
        assert len(summary) == 10
        keys = ["_id", "user_name", "order_items", "quantities", "total_spending"]
        assert all(key in datas["users_orders"] for key in keys for datas in summary)

    @pytest.mark.asyncio
    async def test_mongodb_cyclic_source(self):
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_mongodb_cyclic_source.xml", capture_test_result=True
        )
        await test_engine.test_with_timer()

        result = test_engine.capture_result()
        mongo_func_test = result["mongo_func_test"]
        assert len(mongo_func_test) == 5

        mongo_selector = result["mongo_selector"]
        assert len(mongo_selector) == 10
        for m in mongo_selector:
            assert "user_id" in m
            assert m["user_id"] in range(1, 6)
            assert "user_name" in m
            assert m["user_name"] in ["Bob", "Frank", "Phil"]
            assert "_id" not in m

        variable_select_mongo = result["variable_select_mongo"]
        assert len(variable_select_mongo) == 20
        for m in mongo_selector:
            assert "user_id" in m
            assert m["user_id"] in range(1, 6)
            assert "user_name" in m
            assert m["user_name"] in ["Bob", "Frank", "Phil"]
            assert "_id" not in m

        variable_select_non_cyclic = result["variable_select_non_cyclic"]
        assert len(variable_select_non_cyclic) == 5
        for m in mongo_selector:
            assert "user_id" in m
            assert m["user_id"] in range(1, 6)
            assert "user_name" in m
            assert m["user_name"] in ["Bob", "Frank", "Phil"]
            assert "_id" not in m

    @pytest.mark.asyncio
    async def test_mongodb_with_type(self):
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_mongodb_with_type.xml", capture_test_result=True
        )
        await test_engine.test_with_timer()

        result = test_engine.capture_result()

        range_list = list(range(1, 21))

        mongo_func_test = result["mongo_func_test"]
        assert len(mongo_func_test) == 20

        mongo_data = result["mongo_data"]
        assert len(mongo_data) == 20
        for m in mongo_data:
            assert "id" in m
            assert m["id"] in range_list
            assert "name" in m
            assert m["name"] in ["Bob", "Frank", "Phil"]
            assert "_id" not in m
        assert any(a["id"] != b for a, b in zip(mongo_data, range_list))

        data_ordered = result["data_ordered"]
        assert len(data_ordered) == 20
        for m in data_ordered:
            assert "id" in m
            assert m["id"] in range_list
            assert "name" in m
            assert m["name"] in ["Bob", "Frank", "Phil"]
            assert "_id" not in m
        assert all(a["id"] == b for a, b in zip(data_ordered, range_list))

        mongo_selector = result["mongo_selector"]
        assert len(mongo_selector) == 20
        for m in mongo_selector:
            assert "user_id" in m
            assert m["user_id"] in range_list
            assert "user_name" in m
            assert m["user_name"] in ["Bob", "Frank", "Phil"]
            assert "_id" in m
            assert isinstance(m["_id"], ObjectId)
        assert any(a["user_id"] != b for a, b in zip(mongo_selector, range_list))

        mongo_selector_ordered = result["mongo_selector_ordered"]
        assert len(mongo_selector_ordered) == 20
        for m in mongo_selector_ordered:
            assert "user_id" in m
            assert m["user_id"] in range_list
            assert "user_name" in m
            assert m["user_name"] in ["Bob", "Frank", "Phil"]
            assert "_id" in m
            assert isinstance(m["_id"], ObjectId)
        assert all(a["user_id"] == b for a, b in zip(mongo_selector_ordered, range_list))
