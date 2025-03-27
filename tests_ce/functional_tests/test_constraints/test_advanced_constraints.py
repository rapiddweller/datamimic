# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path
from unittest import TestCase

from datamimic_ce.data_mimic_test import DataMimicTest


class TestAdvancedConstraints(TestCase):
    _test_dir = Path(__file__).resolve().parent

    def test_nested_key_filtering_constraints(self):
        """
        Test constraints in nested keys with filtering conditions.

        This test validates that filtering conditions work correctly in nested keys,
        ensuring that records not matching conditions are filtered out.
        """
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_nested_key_filtering.xml", capture_test_result=True
        )
        engine.test_with_timer()
        result = engine.capture_result()

        # Verify primary output
        nested_data = result["nested_container"]
        self.assertEqual(len(nested_data), 1)

        # Check the filtered data
        high_risk_customers = nested_data[0]["filtered_high_risk"]
        self.assertGreater(len(high_risk_customers), 0)

        # Verify all high_risk customers have credit_score < 600
        for customer in high_risk_customers:
            self.assertLess(customer["credit_score"], 600)
            self.assertEqual(customer["risk_profile"], "High")

        # Check the complementary filtered data
        non_high_risk = nested_data[0]["non_high_risk"]
        self.assertGreater(len(non_high_risk), 0)

        # Verify all non-high risk customers have credit_score >= 600
        for customer in non_high_risk:
            self.assertGreaterEqual(customer["credit_score"], 600)
            self.assertIn(customer["risk_profile"], ["Medium", "Low"])

    def test_multi_level_filtering_chain(self):
        """
        Test chain of filtering constraints across multiple levels.

        This test validates that multiple levels of filtering work correctly in sequence,
        with each level building on the results of the previous level.
        """
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_multi_level_filtering.xml", capture_test_result=True
        )
        engine.test_with_timer()
        result = engine.capture_result()

        # Verify results from multi-level filtering
        filtering_result = result["multi_level_filtering"]
        self.assertEqual(len(filtering_result), 1)

        # Final filtered results should only have customers that match all criteria
        final_approved = filtering_result[0]["final_approved"]
        self.assertGreater(len(final_approved), 0)

        # Check final filtered customers meet all criteria
        for customer in final_approved:
            # Should have sufficient income to be worth additional processing
            self.assertGreaterEqual(customer["income"], 40000)

    def test_complex_boolean_expressions(self):
        """
        Test constraints with complex boolean expressions.

        This test validates that constraints can handle complex boolean expressions
        including AND, OR, and NOT operations.
        """
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_complex_boolean.xml", capture_test_result=True)
        engine.test_with_timer()
        result = engine.capture_result()

        # Verify results with complex boolean filtering
        boolean_results = result["complex_boolean_filtering"]
        self.assertGreater(len(boolean_results), 0)

        # Check special category with complex conditions
        for item in boolean_results:
            if "special_category" in item and item["special_category"] == True:
                # This should satisfy the complex boolean expression:
                # (high income OR perfect credit) AND young
                high_income = item["income"] >= 100000
                perfect_credit = item["credit_score"] >= 800
                young = item["age"] < 30

                # Verify the complex condition
                self.assertTrue((high_income or perfect_credit) and young)

    def test_constraint_combinations(self):
        """
        Test combinations of source constraints, mapping, and target constraints.

        This test validates that different constraint types can be combined
        and applied in sequence, with each building upon the results of previous stages.
        """
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_constraint_combinations.xml", capture_test_result=True
        )
        engine.test_with_timer()
        result = engine.capture_result()

        # Verify processed data after multiple constraint types
        processed_data = result["combined_constraints"]
        self.assertGreater(len(processed_data), 0)

        # For each record that made it through all constraints
        for record in processed_data:
            # Verify source constraints were applied (classification)
            if record["income"] < 30000:
                self.assertEqual(record["income_category"], "Low")
            elif record["income"] < 100000:
                self.assertEqual(record["income_category"], "Medium")
            else:
                self.assertEqual(record["income_category"], "High")

            # Verify mapping was applied (calculation)
            self.assertEqual(record["max_loan"], record["income"] * 0.4)

            # Verify target constraints were applied (filtering)
            # Only records with sufficient income and credit remained
            self.assertGreaterEqual(record["income"], 20000)
            self.assertGreaterEqual(record["credit_score"], 500)

    def test_nested_conditional_filtering(self):
        """
        Test nested keys with various conditional filtering approaches.

        This test validates that different filtering conditions work correctly
        in nested keys, including simple conditions, compound conditions,
        and negative conditions.
        """
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_nested_conditional_filtering.xml", capture_test_result=True
        )
        engine.test_with_timer()
        result = engine.capture_result()

        # Verify results from nested conditional filtering
        container = result["nested_filtering_container"]
        self.assertEqual(len(container), 1)

        # Test 1: High income filtering
        high_income = container[0]["high_income"]
        self.assertGreater(len(high_income), 0)
        for customer in high_income:
            self.assertGreaterEqual(customer["income"], 100000)

        # Test 2: Good credit filtering
        good_credit = container[0]["good_credit"]
        self.assertGreater(len(good_credit), 0)
        for customer in good_credit:
            self.assertGreaterEqual(customer["credit_score"], 720)

        # Test 3: Premium customers (AND condition)
        premium = container[0]["premium_customers"]
        self.assertGreater(len(premium), 0)
        for customer in premium:
            self.assertGreaterEqual(customer["income"], 100000)
            self.assertGreaterEqual(customer["credit_score"], 720)

        # Test 4: Young or wealthy customers (OR condition)
        young_or_wealthy = container[0]["young_or_wealthy"]
        self.assertGreater(len(young_or_wealthy), 0)
        for customer in young_or_wealthy:
            self.assertTrue(customer["age"] < 30 or customer["income"] >= 150000)

        # Test 5: Not high risk customers (NOT condition)
        not_high_risk = container[0]["not_high_risk"]
        self.assertGreater(len(not_high_risk), 0)
        for customer in not_high_risk:
            self.assertGreaterEqual(customer["credit_score"], 600)
            self.assertIn(customer["risk_category"], ["Medium", "Low"])

    def test_equality_filtering(self):
        """
        Test filtering based on equality comparisons.

        This test validates that filtering based on equality comparisons works correctly,
        including exact matches on categorical and numeric values, compound equality conditions,
        and inequality conditions.
        """
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_equality_filtering.xml", capture_test_result=True
        )
        engine.test_with_timer()
        result = engine.capture_result()

        # Verify results from equality filtering
        container = result["equality_filtering_results"]
        self.assertEqual(len(container), 1)

        # Test 1: Exact match on categorical value
        exact_match_category = container[0]["exact_match_category"]
        self.assertGreater(len(exact_match_category), 0)
        for customer in exact_match_category:
            self.assertEqual(customer["customer_type"], "Premium")

        # Test 2: Exact match on numeric value
        exact_match_numeric = container[0]["exact_match_numeric"]
        self.assertGreater(len(exact_match_numeric), 0)
        for customer in exact_match_numeric:
            self.assertEqual(customer["age"], 30)

        # Test 3: Compound equality with AND
        compound_equality = container[0]["compound_equality"]
        self.assertGreater(len(compound_equality), 0)
        for customer in compound_equality:
            self.assertEqual(customer["risk_profile"], "Low")
            self.assertEqual(customer["status"], "Active")

        # Test 4: Multiple equality conditions with OR
        multiple_equalities = container[0]["multiple_equalities"]
        self.assertGreater(len(multiple_equalities), 0)
        for customer in multiple_equalities:
            self.assertTrue(
                customer["region"] == "North" or customer["region"] == "South" or customer["risk_profile"] == "Low"
            )

        # Test 5: Inequality filtering
        inequality_filtering = container[0]["inequality_filtering"]
        self.assertGreater(len(inequality_filtering), 0)
        for customer in inequality_filtering:
            self.assertNotEqual(customer["region"], "East")
            self.assertNotEqual(customer["region"], "West")
            self.assertIn(customer["region"], ["North", "South"])
