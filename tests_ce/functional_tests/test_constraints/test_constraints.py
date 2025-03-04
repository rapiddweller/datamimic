# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path
from unittest import TestCase

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest


class TestConstraints(TestCase):
    _test_dir = Path(__file__).resolve().parent

    def test_constraints(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_constraints.xml", capture_test_result=True)
        engine.test_with_timer()
        result = engine.capture_result()

        synthetic_customers = result["synthetic_customers"]
        assert len(synthetic_customers) == 100
        for ele in synthetic_customers:
            if ele["credit_score"] < 600:
                assert ele["risk_profile"] == 'High'
            elif 600 <= ele["credit_score"] < 750:
                assert ele["risk_profile"] == 'Medium'
            else:
                assert ele["risk_profile"] == 'Low'
