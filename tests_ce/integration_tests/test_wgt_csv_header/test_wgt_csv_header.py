# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""A '.wgt.csv' (value|weight) source now accepts an OPTIONAL header row - auto-detected: if the
first row's weight column isn't numeric, it's a header and gets skipped. The pre-existing
headerless format keeps working unchanged."""

from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest

_dir = Path(__file__).resolve().parent


def _run():
    engine = DataMimicTest(test_dir=_dir, filename="wgt_csv_header.xml", capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()


def test_wgt_csv_with_header_applies_weights():
    result = _run()
    rows = result["with_header"]
    true_count = sum(1 for r in rows if r["active"])
    ratio = true_count / len(rows)
    assert 0.7 < ratio < 0.9, f"expected ~80% true, got {ratio:.1%}"


def test_wgt_csv_without_header_still_works():
    """Regression: the pre-existing headerless format must keep working unchanged."""
    result = _run()
    rows = result["no_header"]
    true_count = sum(1 for r in rows if r["active"])
    ratio = true_count / len(rows)
    assert 0.7 < ratio < 0.9, f"expected ~80% true, got {ratio:.1%}"
