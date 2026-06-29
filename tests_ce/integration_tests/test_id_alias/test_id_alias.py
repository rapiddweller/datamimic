# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""<id> is a human-readable alias of <key>.

Surface: engine (datamimic_ce). Proves <id> parses (L1) and produces data identical
to <key> (L3), including the common <id generator="IncrementGenerator"> pattern that
Benerator descriptors use for sequence/DB-sequence identifiers.
"""

from __future__ import annotations

from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest

_TEST_DIR = Path(__file__).resolve().parent


def test_id_equals_key():
    engine = DataMimicTest(test_dir=_TEST_DIR, filename="id_equivalence.xml", capture_test_result=True)
    engine.test_with_timer()
    rows = engine.capture_result()["rows"]
    assert [r["via_id"] for r in rows] == [r["via_key"] for r in rows] == ["42"] * 5
    assert [r["seq"] for r in rows] == [1, 2, 3, 4, 5]  # <id> drives an identifier generator
