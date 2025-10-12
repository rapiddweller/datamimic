# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


class TestPrefixedWeightedIntPagination:
    _test_dir = Path(__file__).resolve().parent

    def test_prefixed_weighted_int_across_pages(self):
        """
        Verify PrefixedWeightedInt maintains monotonic sequences across page boundaries.

        The descriptor is configured with:
        - count=100
        - pageSize=10
        - target=ConsoleExporter

        We still capture results via TestResultExporter (capture_test_result=True)
        to avoid parsing console output. This validates that generator caching
        keeps state across the 10 page boundaries.
        """
        engine = DataMimicTest(
            test_dir=self._test_dir,
            filename="prefixed_weighted_int_pagination.xml",
            capture_test_result=True,
        )
        engine.test_with_timer()

        # Product name in the XML is 'customers'
        result = engine.capture_result()["customers"]

        # Expect exactly 100 records (10 pages x 10 rows)
        assert len(result) == 100

        # Extract numeric parts
        c_vals = [int(r["custId_seq"][1:]) for r in result]
        s_vals = [int(r["custId_seq_WI"][1:]) for r in result]
        a_vals = [int(r["custId_sparse"][1:]) for r in result]

        # C and S should both be strictly increasing by 1 and identical
        assert c_vals == list(range(1, 101)), "custId_seq should be C1..C100"
        assert s_vals == list(range(1, 101)), "custId_seq_WI should be S1..S100"
        assert c_vals == s_vals, "custId_seq_WI must mirror custId_seq"

        # A must be strictly increasing (no resets at page boundaries)
        assert all(b > a for a, b in zip(a_vals, a_vals[1:], strict=False)), (
            "custId_sparse must strictly increase across all records"
        )

        # Spot-check page boundary continuity for sparse IDs (indexes 10->11, 20->21, ...)
        page_size = 10
        for boundary in range(page_size, len(a_vals), page_size):
            assert a_vals[boundary] > a_vals[boundary - 1], (
                f"custId_sparse should continue increasing at page boundary index {boundary}"
            )
