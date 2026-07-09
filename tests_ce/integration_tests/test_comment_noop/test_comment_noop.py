# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""<comment> is an ignored documentation-only element (legacy DSL compatibility).

Surface: engine (datamimic_ce). Proves a model with <comment> elements (at setup
level and nested inside <generate>, between fields) parses (L1) and produces data
identical to the same model with the comments removed (the no-op proof).
"""

from __future__ import annotations

from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest

_TEST_DIR = Path(__file__).resolve().parent


def _run(filename: str) -> dict:
    engine = DataMimicTest(test_dir=_TEST_DIR, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()


def test_comment_is_noop():
    with_comments = _run("comment_noop.xml")["people"]
    baseline = _run("comment_baseline.xml")["people"]
    assert with_comments == baseline
    assert [row["i"] for row in baseline] == [1, 2, 3]
    assert all(row["label"] == "x" for row in baseline)
