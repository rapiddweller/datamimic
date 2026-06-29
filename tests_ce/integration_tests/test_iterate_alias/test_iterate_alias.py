# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""<iterate> is a human-readable alias of <generate>.

Surface: engine (datamimic_ce). Proves <iterate source=...> parses (L1) and produces
data identical to the equivalent <generate source=...> (L3), and that it is a valid
nested child of <generate>.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest

_TEST_DIR = Path(__file__).resolve().parent


def _run(filename: str) -> dict:
    engine = DataMimicTest(test_dir=_TEST_DIR, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()


def test_iterate_equals_generate():
    res = _run("iterate_equivalence.xml")
    via_generate = [row["v"] for row in res["via_generate"]]
    via_iterate = [row["v"] for row in res["via_iterate"]]
    expected = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]  # CSV values are strings
    assert via_iterate == via_generate == expected


def test_iterate_nested_in_generate():
    res = _run("iterate_nested.xml")
    assert [row["id"] for row in res["outer"]] == [1, 2, 3]
    children = res["children"]  # nested products are captured under their own key, flattened
    assert len(children) == 6  # 3 outer rows x 2 ordered source rows
    assert all(c["tag"] == "x" for c in children)
    assert [c["v"] for c in children] == ["0", "1"] * 3  # ordered -> first 2 rows each time


def test_sourceless_iterate_rejected():
    # <iterate> is the source-driven alias; without a source it must fail at parse.
    with pytest.raises(Exception, match="iterate.*requires.*source"):
        _run("iterate_no_source.xml")
