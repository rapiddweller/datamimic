# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Same-named statements with different sources must not share a cached source length.
Regression for the shop-demo truncation: the second <iterate name="products"> inherited
the first one's cached length (3) and silently dropped its 4th row."""

from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest

_TEST_DIR = Path(__file__).resolve().parent


def test_same_name_different_source_lengths_do_not_collide():
    engine = DataMimicTest(test_dir=_TEST_DIR, filename="collision.xml", capture_test_result=True)
    engine.test_with_timer()
    rows = engine.capture_result()["products"]

    # The 4th row of the SECOND source must survive; with a name-only cache key the
    # second statement reads only 3 rows and 'Evian' never appears anywhere.
    assert any(r["name"] == "Evian" for r in rows), (
        f"second statement was truncated to the first statement's cached length; got {len(rows)} rows"
    )
