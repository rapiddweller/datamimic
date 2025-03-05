# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path
from unittest import TestCase

from datamimic_ce.data_mimic_test import DataMimicTest


class TestConstraints(TestCase):
    _test_dir = Path(__file__).resolve().parent

    def test_constraints(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_constraints.xml", capture_test_result=True)
        engine.test_with_timer()
        result = engine.capture_result()

        synthetic_customers = result["synthetic_customers"]
        assert len(synthetic_customers) == 10000
        for ele in synthetic_customers:
            assert isinstance(ele["id"], int)
            assert ele["id"] in range(1, 10001)
            if ele["credit_score"] < 600:
                assert ele["risk_profile"] == 'High'
            elif 600 <= ele["credit_score"] < 750:
                assert ele["risk_profile"] == 'Medium'
            else:
                assert ele["risk_profile"] == 'Low'

    def test_constraints_non_cyclic(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_constraints_non_cyclic.xml", capture_test_result=True)
        engine.test_with_timer()
        result = engine.capture_result()

        original_customers = result["original_customers"]
        assert len(original_customers) == 100
        assert any(customer["risk_profile"] != 'High' for customer in original_customers
                   if customer["credit_score"] < 600)
        assert any(customer["risk_profile"] != 'Medium' for customer in original_customers
                   if 600 <= customer["credit_score"] < 750)
        assert any(customer["risk_profile"] != 'Low' for customer in original_customers
                   if customer["credit_score"] >= 750)
        assert all(customer["id"] is not None for customer in original_customers)

        # filtered generate
        constraints_customers = result["constraints_customers"]
        assert len(constraints_customers) < 100

        for ele in constraints_customers:
            assert isinstance(ele["id"], int)
            assert ele["id"] in range(1, 101)
            if ele["credit_score"] < 600:
                assert ele["risk_profile"] == 'High'
            elif 600 <= ele["credit_score"] < 750:
                assert ele["risk_profile"] == 'Medium'
            else:
                assert ele["risk_profile"] == 'Low'

    def test_constraints_order_distribution(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_constraints_order_distribution.xml", capture_test_result=True)
        engine.test_with_timer()
        result = engine.capture_result()

        synthetic_customers = result["synthetic_customers"]
        assert len(synthetic_customers) == 100
        for ele in synthetic_customers:
            assert isinstance(ele["id"], int)
            assert ele["id"] in range(1, 101)
            if ele["credit_score"] < 600:
                assert ele["risk_profile"] == 'High'
            elif 600 <= ele["credit_score"] < 750:
                assert ele["risk_profile"] == 'Medium'
            else:
                assert ele["risk_profile"] == 'Low'

    def test_constraints_single_processing(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_constraints_single_processing.xml", capture_test_result=True)
        engine.test_with_timer()
        result = engine.capture_result()

        synthetic_customers = result["synthetic_customers"]
        assert len(synthetic_customers) == 100
        for ele in synthetic_customers:
            assert isinstance(ele["id"], int)
            assert ele["id"] in range(1, 101)
            if ele["credit_score"] < 600:
                assert ele["risk_profile"] == 'High'
            elif 600 <= ele["credit_score"] < 750:
                assert ele["risk_profile"] == 'Medium'
            else:
                assert ele["risk_profile"] == 'Low'
