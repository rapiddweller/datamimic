# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path
from unittest import TestCase

from datamimic_ce.data_mimic_test import DataMimicTest


class TestMappingTargetConstraints(TestCase):
    _test_dir = Path(__file__).resolve().parent

    def test_mapping_target_constraints(self):
        """
        Test the full constraints workflow with source constraints, mapping, and target constraints.

        This test validates the three-layer constraints system:
        1. Source constraints - filtering and initial classification
        2. Mapping - transforming data based on classifications and attributes
        3. Target constraints - final validation and adjustments
        """
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_mapping_target_constraints.xml", capture_test_result=True
        )
        engine.test_with_timer()
        result = engine.capture_result()

        customers = result["customers_with_constraints"]
        assert len(customers) == 100

        # Convert string values to appropriate numeric types for testing
        for customer in customers:
            for key in ["income", "years_employed", "credit_score", "interest_rate", "credit_limit"]:
                if key in customer and isinstance(customer[key], str):
                    try:
                        # Try to convert to int first
                        if customer[key].isdigit() or (customer[key].startswith("-") and customer[key][1:].isdigit()):
                            customer[key] = int(customer[key])
                        # Then try float
                        else:
                            try:
                                customer[key] = float(customer[key])
                            except ValueError:
                                pass  # Keep as string if conversion fails
                    except (AttributeError, ValueError):
                        pass  # Keep as is if any error occurs

        # Debug: Print key values from the first customer
        print("\nDEBUG - First customer record (after type conversion):")
        print(f"income type: {type(customers[0]['income'])} value: {customers[0]['income']}")
        print(f"years_employed type: {type(customers[0]['years_employed'])} value: {customers[0]['years_employed']}")
        print(
            f"credit_limit type: {type(customers[0]['credit_limit']) if 'credit_limit' in customers[0] else 'N/A'} value: {customers[0]['credit_limit'] if 'credit_limit' in customers[0] else 'N/A'}"
        )
        print(f"All keys in first record: {customers[0].keys()}")

        # Print mapping rules that should have been executed
        if customers[0]["income"] > 50000 and customers[0]["years_employed"] > 2:
            print("Rule should match: income > 50000 and years_employed > 2 -> credit_limit = 25000")
            print("But actual credit_limit is:", customers[0]["credit_limit"])
        else:
            print(f"Rule didn't match: {customers[0]['income']} > 50000 and {customers[0]['years_employed']} > 2")

        # Verify source constraints were applied correctly
        risk_profile_hight, risk_profile_medium, risk_profile_low = 0, 0, 0
        interest_rate_high, interest_rate_medium, interest_rate_low = 0, 0, 0
        credit_limit_very_high, credit_limit_high, credit_limit_medium, credit_limit_low = 0, 0, 0, 0
        approval_status_high, approval_status_medium, approval_status_low = 0, 0, 0

        for customer in customers:
            assert isinstance(customer["id"], int)
            assert customer["id"] in range(1, 101)

            # If credit_limit is missing, print diagnostic info
            if "credit_limit" not in customer:
                print(f"\nMissing credit_limit for record {customer['id']}:")
                print(f"income: {customer['income']}, years_employed: {customer['years_employed']}")
                print(f"All keys: {customer.keys()}")
                continue

            # Check source constraints (risk profile assignment)
            if customer["credit_score"] < 600:
                assert customer["risk_profile"] == "High"
                risk_profile_hight += 1
            elif 600 <= customer["credit_score"] < 750:
                assert customer["risk_profile"] == "Medium"
                risk_profile_medium += 1
            else:
                assert customer["risk_profile"] == "Low"
                risk_profile_low += 1

            # Check mapping rules (interest rates)
            if customer["risk_profile"] == "High":
                assert customer["interest_rate"] == 0.15
                interest_rate_high += 1
            elif customer["risk_profile"] == "Medium":
                assert customer["interest_rate"] == 0.10
                interest_rate_medium += 1
            elif customer["risk_profile"] == "Low":
                assert customer["interest_rate"] == 0.05
                interest_rate_low += 1

            # Check mapping rules (credit limits)
            if customer["income"] > 100000 and customer["years_employed"] > 5:
                assert customer["credit_limit"] == 50000
                credit_limit_very_high += 1
            elif customer["income"] > 50000 and customer["years_employed"] > 2:
                assert customer["credit_limit"] == 25000
                credit_limit_high += 1
            elif customer["income"] > 30000:
                assert customer["credit_limit"] == 10000
                credit_limit_medium += 1
            elif customer["income"] <= 30000:
                assert customer["credit_limit"] == 5000
                credit_limit_low += 1

            # Check target constraints (approval status)
            if customer["credit_limit"] >= 25000 and customer["interest_rate"] <= 0.08:
                assert customer["approval_status"] == "Approved"
                approval_status_high += 1
            elif 5000 < customer["credit_limit"] < 25000 and customer["interest_rate"] > 0.08:
                assert customer["approval_status"] == "Review"
                approval_status_medium += 1
            elif customer["credit_limit"] <= 5000 and customer["interest_rate"] >= 0.12:
                assert customer["approval_status"] == "Denied"
                approval_status_low += 1

        assert risk_profile_hight > 0
        assert risk_profile_medium > 0
        assert risk_profile_low > 0
        assert interest_rate_high > 0
        assert interest_rate_medium > 0
        assert interest_rate_low > 0
        assert credit_limit_very_high > 0
        assert credit_limit_high > 0
        assert credit_limit_medium > 0
        assert credit_limit_low > 0
        assert approval_status_high > 0
        assert approval_status_medium > 0
        assert approval_status_low > 0

    def test_constraints_sequence(self):
        """
        Test that constraints are applied in the correct sequence:
        1. Source constraints first
        2. Mapping transformations second
        3. Target constraints last

        This ensures that each layer builds upon the previous one correctly.
        """
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_constraints_sequence.xml", capture_test_result=True
        )
        engine.test_with_timer()
        result = engine.capture_result()

        sequence_test_data = result["constraint_sequence_test"]
        assert len(sequence_test_data) == 100

        for item in sequence_test_data:
            assert isinstance(item["id"], int)
            assert item["id"] in range(1, 101)

            # Source constraints should set source_step = 2 directly
            assert item["source_step"] == 2

            # Mapping should add 1 to source_step, making mapping_step = 3
            assert item["mapping_step"] == 3

            # Target constraints should add 1 to mapping_step, making target_step = 4
            assert item["target_step"] == 4

    def test_constraints_dependency(self):
        """
        Test that target constraints can access values created by mapping rules.

        This validates that the constraints pipeline correctly passes information
        from one stage to the next, allowing later stages to build on earlier ones.
        """
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_constraints_dependency.xml", capture_test_result=True
        )
        engine.test_with_timer()
        result = engine.capture_result()

        dependency_test_data = result["dependency_test"]
        assert len(dependency_test_data) == 100

        for item in dependency_test_data:
            assert isinstance(item["id"], int)
            assert item["id"] in range(1, 101)

            # Mapping should create mapped_value = 42
            assert item["mapped_value"] == 42

            # Target constraints should check mapped_value and set target_value if condition is met
            assert item["target_value"] == "success"
