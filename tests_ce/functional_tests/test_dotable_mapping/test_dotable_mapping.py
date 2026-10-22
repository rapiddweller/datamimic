# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest


class TestDotableMapping:
    _test_dir = Path(__file__).resolve().parent

    def test_row_supports_mapping_access_in_scripts(self):
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_dotable_mapping.xml", capture_test_result=True
        )
        test_engine.test_with_timer()
        result = test_engine.capture_result()

        rows = result["check"]
        assert len(rows) == 2
        for index, row in enumerate(rows, start=1):
            assert row["by_item"] == index
            assert row["by_dict"] == index
            assert row["field_count"] == 2
            assert row["has_id"] is True
            assert row["missing"] == "none"
            assert row["nested_sku"] == "sku-1"
            assert row["item_count"] == 2
