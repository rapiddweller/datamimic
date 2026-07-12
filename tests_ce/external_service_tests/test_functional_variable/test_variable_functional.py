# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


class TestVariableFunctional:
    _test_dir = Path(__file__).resolve().parent

    def test_query_setup_context_variable(self):
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_query_setup_context_variable.xml", capture_test_result=True
        )
        engine.test_with_timer()
        result = engine.capture_result()
        query_variable_test = result.get("query_variable_test")
        assert len(query_variable_test) == 10
        for element in query_variable_test:
            assert element.get("id") in [1, 2, 3]
            assert element.get("name") in ["Name 1", "Name 2", "Name 3"]
            if element.get("id") == 1:
                assert element.get("name") == "Name 1"
            elif element.get("id") == 2:
                assert element.get("name") == "Name 2"
            elif element.get("id") == 3:
                assert element.get("name") == "Name 3"
            assert element.get("static_id") == 1
            assert element.get("static_name") == "Name 1"

    def test_variable_with_type(self):
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_variable_with_type.xml", capture_test_result=True
        )
        engine.test_with_timer()
        result = engine.capture_result()
        variable_with_type = result["user"]
        assert len(variable_with_type) == 10
        for ele in variable_with_type:
            assert ele.get("table_id") == 1
            assert ele.get("table_name") == "Name 1"
            assert ele.get("table_number") == 1

        user_2 = result["user_2"]
        assert len(user_2) == len(variable_with_type)
        count = 0
        for ele in user_2:
            count += 1
            assert ele.get("id") == count
            assert ele.get("name") == "Name 1"
            assert ele.get("number") == 1

    def test_variable_source_with_name_only(self):
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_variable_source_with_name_only.xml", capture_test_result=True
        )
        engine.test_with_timer()
        result = engine.capture_result()
        variable_with_type = result["user"]
        assert len(variable_with_type) == 10
        for ele in variable_with_type:
            assert ele.get("id") == 1
            assert ele.get("name") == "Name 1"
            assert ele.get("number") == 1

    def test_variable_with_selector_cyclic(self):
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_variable_with_selector_cyclic.xml", capture_test_result=True
        )
        engine.test_with_timer()
        result = engine.capture_result()

        user = result["user"]
        assert len(user) == 3
        assert all(ele.get("id") in [1, 2, 3] for ele in user)

        selector_cyclic = result["selector_cyclic"]
        assert len(selector_cyclic) == 10
        assert all(ele.get("user_id") in [1, 2, 3] for ele in selector_cyclic)
        for ele in selector_cyclic:
            if ele.get("user_id") == 1:
                assert ele.get("user_text") == "Name 1"
            elif ele.get("user_id") == 2:
                assert ele.get("user_text") == "Name 2"
            elif ele.get("user_id") == 3:
                assert ele.get("user_text") == "Name 3"

        iteration_selector_cyclic = result["iteration_selector_cyclic"]
        assert len(iteration_selector_cyclic) == 10
        for ele in iteration_selector_cyclic:
            if ele.get("user_id") == 1:
                assert ele.get("user_text") == "Name 1"
            elif ele.get("user_id") == 2:
                assert ele.get("user_text") == "Name 2"
            elif ele.get("user_id") == 3:
                assert ele.get("user_text") == "Name 3"

        # unique= is likewise a no-op for iterationSelector (same reason cyclic is): every
        # record re-runs the query fresh and gets the full 3-row result, never a distinct subset.
        iteration_selector_unique = result["iteration_selector_unique"]
        assert len(iteration_selector_unique) == 5
        assert all(ele.get("row_count") == 3 for ele in iteration_selector_unique)

    def test_variable_selector_distribution_matrix(self):
        """<variable selector=...> distribution x unique cells not covered by
        test_variable_with_selector_cyclic (which only exercises distribution="ordered")."""
        engine = DataMimicTest(
            test_dir=self._test_dir,
            filename="test_variable_selector_distribution_matrix.xml",
            capture_test_result=True,
        )
        engine.test_with_timer()
        result = engine.capture_result()

        random_ids = [r["row_id"] for r in result["selector_random"]]
        # default distribution="random" is a shuffle (permutation, no replacement): count == pool
        assert len(random_ids) == 15
        assert set(random_ids) == set(range(1, 16)), f"expected a permutation of 1..15, got {sorted(random_ids)}"

        cyclic_random_ids = [r["row_id"] for r in result["selector_cyclic_random"]]
        assert len(cyclic_random_ids) == 30
        assert set(cyclic_random_ids) <= set(range(1, 16)), (
            f"every id must come from the seeded 1..15 pool: {set(cyclic_random_ids)}"
        )
        # cyclic=true wraps the shuffled order once count (30) exceeds the pool (15): repeats required
        assert len(set(cyclic_random_ids)) < 30

        cumulated_ids = [r["row_id"] for r in result["selector_cumulated"]]
        assert len(cumulated_ids) == 15
        assert set(cumulated_ids) <= set(range(1, 16)), f"every id must come from the seeded pool: {set(cumulated_ids)}"
        # bell-weighted with replacement: a full 1..15 permutation would mean this collapsed to
        # uniform-without-replacement instead of an actual weighted draw
        assert len(set(cumulated_ids)) < 15

        unique_ids = [r["row_id"] for r in result["selector_unique"]]
        assert len(unique_ids) == 15
        assert set(unique_ids) == set(range(1, 16)), f"expected all 15 pool values exactly once, got {sorted(unique_ids)}"

        # spot-check: <variable type=...> against RDBMS hits the same variable_task.py branch
        # already matrix-tested for MongoDB - pageSize (5) < count (15) is the exact shape of the
        # original truncation bug (loads_all must ignore pageSize and read the whole table).
        type_random_ids = [r["row_id"] for r in result["type_random_paged"]]
        assert len(type_random_ids) == 15
        assert set(type_random_ids) == set(range(1, 16)), (
            f"expected the full 1..15 pool despite pageSize=5, got {sorted(type_random_ids)}"
        )

        type_cyclic_ids = [r["row_id"] for r in result["type_cyclic_ordered"]]
        # stable order 1..15, wrapped: 1..15 then 1..7
        assert type_cyclic_ids == [*range(1, 16), *range(1, 8)], type_cyclic_ids
