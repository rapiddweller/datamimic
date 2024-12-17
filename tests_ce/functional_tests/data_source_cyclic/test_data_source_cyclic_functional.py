# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest
import pytest


class TestDataSourceCyclic:
    _test_dir = Path(__file__).resolve().parent

    @pytest.mark.asyncio
    async def test_csv_cyclic(self):
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_csv_cyclic_mp.xml", capture_test_result=True
        )
        await test_engine.test_with_timer()

        result = test_engine.capture_result()
        cyclic_product = result["cyclic-product"]
        big_cyclic_product = result["big-cyclic-product"]
        non_cyclic_product = result["non-cyclic-product"]

        assert len(non_cyclic_product) == 11

        assert len(cyclic_product) == 20
        assert cyclic_product[9]["ean_code"] == "10"
        assert all(cyclic_product[idx]["ean_code"] == str(idx + 1) for idx in range(0, 11))
        assert all(cyclic_product[idx]["ean_code"] == str((idx + 1) % 11) for idx in range(11, 20))

        assert len(big_cyclic_product) == 100
        assert list(map(lambda product: product["ean_code"], big_cyclic_product)).count("1") == 10
        assert list(map(lambda product: product["ean_code"], big_cyclic_product)).count("11") == 9
        assert list(map(lambda product: product["ean_code"], big_cyclic_product)).count("5") == 9

        engine_non_mp = DataMimicTest(
            test_dir=self._test_dir, filename="test_csv_cyclic_non_mp.xml", capture_test_result=True
        )
        engine_non_mp.test_with_timer()
        result_non_np = engine_non_mp.capture_result()

        assert result == result_non_np, "CSV cyclic results of mp and non-mp is not equal to each other"

    @pytest.mark.asyncio
    async def test_json_cyclic(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_json_cyclic.xml", capture_test_result=True)
        await test_engine.test_with_timer()

        result = test_engine.capture_result()
        cyclic_product = result["cyclic-product"]
        big_cyclic_product = result["big-cyclic-product"]
        non_cyclic_product = result["non-cyclic-product"]

        assert len(non_cyclic_product) == 12

        assert len(cyclic_product) == 20
        assert cyclic_product[10]["id"] == 11
        assert all(cyclic_product[idx]["id"] == idx + 1 for idx in range(0, 12))
        assert all(cyclic_product[idx]["id"] == (idx + 1) % 12 for idx in range(12, 20))

        assert len(big_cyclic_product) == 100
        assert list(map(lambda product: product["id"], big_cyclic_product)).count(1) == 9
        assert list(map(lambda product: product["id"], big_cyclic_product)).count(2) == 9
        assert list(map(lambda product: product["id"], big_cyclic_product)).count(11) == 8
        assert list(map(lambda product: product["id"], big_cyclic_product)).count(5) == 8

        engine_non_mp = DataMimicTest(
            test_dir=self._test_dir, filename="test_json_cyclic_non_mp.xml", capture_test_result=True
        )
        engine_non_mp.test_with_timer()
        result_non_np = engine_non_mp.capture_result()

        assert result == result_non_np, "JSON cyclic results of mp and non-mp is not equal to each other"

    @pytest.mark.asyncio
    async def test_product_cyclic(self):
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_memstore_product_cyclic.xml", capture_test_result=True
        )
        await test_engine.test_with_timer()

        result = test_engine.capture_result()
        cyclic_product = result["cyclic-product"]
        big_cyclic_product = result["big-cyclic-product"]
        non_cyclic_product = result["non-cyclic-product"]

        assert len(non_cyclic_product) == 15

        assert len(cyclic_product) == 30
        assert cyclic_product[14]["id"] == 15
        assert all(cyclic_product[idx]["id"] == idx + 1 for idx in range(0, 15))
        assert all(cyclic_product[idx]["id"] == idx % 15 + 1 for idx in range(15, 30))

        assert len(big_cyclic_product) == 100
        assert list(map(lambda product: product["id"], big_cyclic_product)).count(1) == 7
        assert list(map(lambda product: product["id"], big_cyclic_product)).count(2) == 7
        assert list(map(lambda product: product["id"], big_cyclic_product)).count(11) == 6
        assert list(map(lambda product: product["id"], big_cyclic_product)).count(10) == 7

        engine_non_mp = DataMimicTest(
            test_dir=self._test_dir, filename="test_memstore_product_cyclic_non_mp.xml", capture_test_result=True
        )
        engine_non_mp.test_with_timer()
        result_non_np = engine_non_mp.capture_result()

        assert list(map(lambda product: product["id"], result_non_np["big-cyclic-product"])) == list(
            map(lambda product: product["id"], big_cyclic_product)
        ), "Memstore cyclic results of mp and non-mp is not equal to each other"

    @pytest.mark.asyncio
    async def test_variable_database_cyclic(self):
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_variable_database_cyclic.xml", capture_test_result=True
        )
        await test_engine.test_with_timer()

        result = test_engine.capture_result()
        non_cyclic_var_db = result["non-cyclic-var-db"]
        non_cyclic_var_db_2 = result["non-cyclic-var-db-2"]
        cyclic_var_db = result["cyclic-var-db"]
        cyclic_var_db_2 = result["cyclic-var-db-2"]
        big_cyclic_var_db_2 = result["big-cyclic-var-db-2"]

        assert len(non_cyclic_var_db) == 17
        assert len(non_cyclic_var_db_2) == 10
        assert len(cyclic_var_db) == 20
        assert len(cyclic_var_db_2) == 20

        assert all(cyclic_var_db[idx]["user_id"] == idx + 1 for idx in range(0, 17))
        assert all(cyclic_var_db_2[idx]["user_id"] == idx % 10 + 6 for idx in range(0, 20))

        assert len(big_cyclic_var_db_2) == 100
        assert list(map(lambda product: product["user_id"], big_cyclic_var_db_2)).count(6) == 9
        assert list(map(lambda product: product["user_id"], big_cyclic_var_db_2)).count(7) == 9
        assert list(map(lambda product: product["user_id"], big_cyclic_var_db_2)).count(17) == 8
        assert list(map(lambda product: product["user_id"], big_cyclic_var_db_2)).count(10) == 8

        engine_non_mp = DataMimicTest(
            test_dir=self._test_dir, filename="test_variable_database_cyclic_non_mp.xml", capture_test_result=True
        )
        engine_non_mp.test_with_timer()
        result_non_np = engine_non_mp.capture_result()

        assert result == result_non_np, "RDBMS cyclic results of mp and non-mp is not equal to each other"

    @pytest.mark.asyncio
    async def test_part_cyclic(self):
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_part_cyclic_mp.xml", capture_test_result=True
        )
        await test_engine.test_with_timer()

        result = test_engine.capture_result()
        people = result["people"]
        assert len(people) == 10

        assert all(len(people[idx]["product-cyclic"]) == 100 for idx in range(0, 10))
        assert all(len(people[idx]["people-cyclic"]) == 100 for idx in range(0, 10))

        for p in people:
            assert all(p["product-cyclic"][x]["gender"] == "male" for x in range(0, 100, 11))
            assert all(p["product-cyclic"][x]["gender"] == "female" for x in range(1, 100, 11))
            assert all(p["product-cyclic"][x]["gender"] == "unisex" for x in range(5, 100, 11))

            assert all(p["people-cyclic"][x]["name"] == "Alice" for x in range(0, 100, 12))
            assert all(p["people-cyclic"][x]["id"] == 1 for x in range(0, 100, 12))
            assert all(p["people-cyclic"][x]["name"] == "Franz" for x in range(5, 100, 12))
            assert all(p["people-cyclic"][x]["id"] == 6 for x in range(5, 100, 12))

    @pytest.mark.asyncio
    async def test_part_no_cyclic(self):
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_part_no_cyclic.xml", capture_test_result=True
        )
        await test_engine.test_with_timer()
        result = test_engine.capture_result()

        people_no_cyclic = result["people_no_cyclic"]
        assert len(people_no_cyclic) == 10
        assert all(len(people_no_cyclic[idx]["product_csv"]) == 11 for idx in range(0, 10))
        assert all(len(people_no_cyclic[idx]["people_json"]) == 12 for idx in range(0, 10))

    @pytest.mark.asyncio
    async def test_part_memstore_cyclic(self):
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_part_memstore_cyclic.xml", capture_test_result=True
        )
        await test_engine.test_with_timer()
        result = test_engine.capture_result()

        # simple source data
        product = result["product"]
        part_test = result["part_mem_test"]

        assert len(part_test) == 10
        source_len = len(product)
        count = 30

        for idx in range(len(part_test)):
            count_not_define = part_test[idx].get("count_not_define")
            non_cyclic_product = part_test[idx].get("non_cyclic_product")
            cyclic_product = part_test[idx].get("cyclic_product")

            assert len(count_not_define) == source_len
            assert len(non_cyclic_product) == min(count, source_len)
            assert len(cyclic_product) == count

        # csv source data
        product_csv = result["product_csv"]
        part_csv_test = result["part_mem_csv_test"]

        assert len(part_csv_test) == 20
        csv_source_len = len(product_csv)
        csv_count = 40

        for idx in range(len(part_csv_test)):
            csv_count_not_define = part_csv_test[idx].get("count_not_define")
            csv_non_cyclic_product = part_csv_test[idx].get("non_cyclic_product")
            csv_cyclic_product = part_csv_test[idx].get("cyclic_product")

            assert len(csv_count_not_define) == csv_source_len
            assert len(csv_non_cyclic_product) == min(csv_count, csv_source_len)
            assert len(csv_cyclic_product) == csv_count

        # JSON source data
        people_json = result["people_json"]
        part_json_test = result["part_mem_json_test"]

        assert len(part_json_test) == 30
        json_source_len = len(people_json)
        json_count = 50

        for idx in range(len(part_json_test)):
            json_count_not_define = part_json_test[idx].get("count_not_define")
            json_non_cyclic_product = part_json_test[idx].get("non_cyclic_product")
            json_cyclic_product = part_json_test[idx].get("cyclic_product")

            assert len(json_count_not_define) == json_source_len
            assert len(json_non_cyclic_product) == min(json_count, json_source_len)
            assert len(json_cyclic_product) == json_count
