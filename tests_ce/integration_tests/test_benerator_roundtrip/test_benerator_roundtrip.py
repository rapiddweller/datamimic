# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# See LICENSE file for the full text of the license.

"""Round-trip proof for the Benerator -> DATAMIMIC converter.

`numbers.datamimic.xml` is the VERBATIM output of the `DatamimicConverter` tool (in the Benerator
project) run on `src/demo/resources/demo/simple/numbers.ben.xml`. This test runs that converted
descriptor through the DATAMIMIC CE engine and asserts it generates — proving the migration
pipeline end-to-end (Benerator descriptor -> converter -> native DATAMIMIC DSL -> CE -> data).

Regenerate the fixture with:
  java -cp <benerator-cp> com.rapiddweller.benerator.main.DatamimicConverter \\
    src/demo/resources/demo/simple/numbers.ben.xml \\
    <this-dir>/numbers.datamimic.xml
"""

from decimal import Decimal
from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest

_TEST_DIR = Path(__file__).resolve().parent


def _run(filename: str, gen: str) -> list[dict]:
    engine = DataMimicTest(test_dir=_TEST_DIR, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()[gen]


def test_converted_numbers_demo_generates_in_datamimic():
    rows = _run("numbers.datamimic.xml", gen="numbers")
    assert len(rows) == 100

    # Benerator type="int" -> DATAMIMIC int
    assert all(isinstance(r["int_max_10"], int) for r in rows)
    # Benerator type="double" + min/max/granularity -> DATAMIMIC float via FloatGenerator, within range/scale
    for r in rows:
        v = r["double_001"]
        assert isinstance(v, float)
        assert 0.0 <= v <= 10.0
        # granularity 0.01 -> at most 2 decimal places
        assert Decimal(str(v)) == Decimal(str(v)).quantize(Decimal("0.01"))
