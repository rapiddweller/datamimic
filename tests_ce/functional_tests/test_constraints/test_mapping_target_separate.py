# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path
from unittest import TestCase

from datamimic_ce.data_mimic_test import DataMimicTest


class TestMappingTargetSeparate(TestCase):
    def setUp(self):
        self._test_dir = Path(__file__).parent

    def test_basic_target_constraints(self):
        """
        Test basic target constraints functionality.

        This test validates that target constraints can properly:
        1. Categorize records based on simple conditions
        2. Make decisions based on multiple factors
        3. Use complex boolean expressions with logical operators
        """
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_basic_target_constraints.xml", capture_test_result=True
        )
        engine.test_with_timer()
        result = engine.capture_result()

        # Verify results
        customers = result["target_constraints_test"]
        self.assertEqual(len(customers), 100)

        # Test risk categorization
        high_risk_count = 0
        medium_risk_count = 0
        low_risk_count = 0

        for customer in customers:
            # Verify risk category assignment
            if customer["credit_score"] < 600:
                self.assertEqual(customer.get("risk_category", "Missing"), "High Risk")
                high_risk_count += 1
            elif 600 <= customer["credit_score"] < 750:
                self.assertEqual(customer.get("risk_category", "Missing"), "Medium Risk")
                medium_risk_count += 1
            else:
                self.assertEqual(customer.get("risk_category", "Missing"), "Low Risk")
                low_risk_count += 1

        # Verify that we have a good distribution of risk categories
        self.assertGreater(high_risk_count, 0, "Should have at least one high risk customer")
        self.assertGreater(medium_risk_count, 0, "Should have at least one medium risk customer")
        self.assertGreater(low_risk_count, 0, "Should have at least one low risk customer")
        self.assertEqual(high_risk_count + medium_risk_count + low_risk_count, 100)

    def test_basic_mapping(self):
        """
        Test basic mapping functionality.

        This test validates that mapping rules can properly:
        1. Calculate dynamic values based on input fields
        2. Perform mathematical operations
        3. Determine interest rates and loan amounts based on customer data
        """
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_basic_mapping.xml", capture_test_result=True)
        engine.test_with_timer()
        result = engine.capture_result()

        # Verify results
        customers = result["mapping_test"]
        self.assertEqual(len(customers), 100)

        for customer in customers:
            # Verify interest rate calculation
            if customer["credit_score"] < 600:
                self.assertAlmostEqual(customer["interest_rate"], 0.15)
            elif 600 <= customer["credit_score"] < 700:
                self.assertAlmostEqual(customer["interest_rate"], 0.12)
            elif 700 <= customer["credit_score"] < 800:
                self.assertAlmostEqual(customer["interest_rate"], 0.09)
            else:
                self.assertAlmostEqual(customer["interest_rate"], 0.06)

            # Verify loan calculation
            expected_loan = 0
            if customer["income"] < 30000:
                expected_loan = customer["income"] * 1.5
            elif 30000 <= customer["income"] < 60000:
                expected_loan = customer["income"] * 2.0
            else:
                expected_loan = customer["income"] * 2.5

            self.assertAlmostEqual(customer["max_loan"], expected_loan)

            # Verify monthly payment calculation
            expected_payment = customer["max_loan"] * customer["interest_rate"] / 12
            self.assertAlmostEqual(customer["monthly_payment"], expected_payment)

    def test_mapping_with_target_constraints(self):
        """
        Test combined mapping and target constraints functionality.

        This test validates that:
        1. Mapping and target constraints can work together in sequence
        2. Target constraints can reference values created during mapping
        3. Complex business logic can be represented through the combination
        """
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_mapping_with_target_constraints.xml", capture_test_result=True
        )
        engine.test_with_timer()
        result = engine.capture_result()

        # Verify results
        customers = result["combined_test"]
        self.assertEqual(len(customers), 100)

        for customer in customers:
            # Verify credit category mappings
            if customer["credit_score"] < 600:
                self.assertEqual(customer.get("credit_category", "Missing"), "Poor")
            elif 600 <= customer["credit_score"] < 700:
                self.assertEqual(customer.get("credit_category", "Missing"), "Fair")
            elif 700 <= customer["credit_score"] < 750:
                self.assertEqual(customer.get("credit_category", "Missing"), "Good")
            else:
                self.assertEqual(customer.get("credit_category", "Missing"), "Excellent")

            # Verify income category mappings
            if customer["income"] < 40000:
                self.assertEqual(customer.get("income_category", "Missing"), "Low")
            elif 40000 <= customer["income"] < 70000:
                self.assertEqual(customer.get("income_category", "Missing"), "Medium")
            else:
                self.assertEqual(customer.get("income_category", "Missing"), "High")

            # Verify max loan calculation based on credit category
            if "credit_category" in customer and "max_loan" in customer:
                multiplier = 0
                if customer["credit_category"] == "Poor":
                    multiplier = 1.5
                elif customer["credit_category"] == "Fair":
                    multiplier = 2.5
                elif customer["credit_category"] == "Good":
                    multiplier = 3.5
                elif customer["credit_category"] == "Excellent":
                    multiplier = 4.5

                expected_max_loan = customer["income"] * multiplier
                self.assertAlmostEqual(customer["max_loan"], expected_max_loan)
