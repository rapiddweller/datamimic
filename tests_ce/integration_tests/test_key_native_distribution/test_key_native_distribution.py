# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Native distribution= on numeric range keys: <key type="int" min= max= distribution="cumulated">
replaces the generator="IntegerGenerator(..., distribution=NumberDistribution.CUMULATED)" eval
string (same DM310 philosophy as native min/max). Numeric range fields only - a non-numeric type
or an unknown distribution value fails at parse time, never silently ignored."""

from pathlib import Path
from statistics import mean

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest

_dir = Path(__file__).resolve().parent


def _run():
    engine = DataMimicTest(_dir, "test_native_distribution.xml", capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()["rows"]


def test_cumulated_int_shapes_a_bell_around_the_midpoint():
    rows = _run()
    scores = [r["score"] for r in rows]
    assert all(isinstance(s, int) and 1 <= s <= 100 for s in scores)
    # symmetric bell, mean = midpoint (50.5): 400 seeded draws land close; uniform would too,
    # so ALSO check concentration - a bell puts far more mass in the middle half than uniform's 50%
    assert abs(mean(scores) - 50.5) < 8
    middle = sum(1 for s in scores if 25 <= s <= 75)
    assert middle / len(scores) > 0.65, f"only {middle}/400 in the middle half - looks uniform, not cumulated"


def test_cumulated_float_and_decimal_respect_range_and_granularity():
    rows = _run()
    prices = [r["price"] for r in rows]
    assert all(0.5 <= p <= 99.5 for p in prices)
    assert all(round(p / 0.5, 6) == int(round(p / 0.5, 6)) for p in prices), "granularity=0.5 violated"
    amounts = [float(r["amount"]) for r in rows]
    assert all(0.01 <= a <= 9.99 for a in amounts)


def test_plain_numeric_key_stays_uniform_by_default():
    rows = _run()
    plains = [r["plain"] for r in rows]
    middle = sum(1 for v in plains if 25 <= v <= 75)
    # uniform: ~51% of mass in [25,75]; a bell would be >65% (see above)
    assert middle / len(plains) < 0.62, "default (no distribution=) must stay uniform"


def test_seeded_runs_replay_identically():
    assert [r["score"] for r in _run()] == [r["score"] for r in _run()]


def test_explicit_uniform_is_valid_and_stays_uniform():
    rows = _run()
    vals = [r["explicit_uniform"] for r in rows]
    assert all(1 <= v <= 100 for v in vals)
    middle = sum(1 for v in vals if 25 <= v <= 75)
    assert middle / len(vals) < 0.62


def test_distribution_without_min_max_is_rejected():
    engine = DataMimicTest(_dir, "test_distribution_without_range.xml", capture_test_result=True)
    with pytest.raises(ValueError, match="(?i)range|min"):
        engine.test_with_timer()


def test_distribution_on_non_numeric_key_is_rejected():
    engine = DataMimicTest(_dir, "test_distribution_wrong_type.xml", capture_test_result=True)
    with pytest.raises(ValueError, match="(?i)distribution"):
        engine.test_with_timer()


def test_unknown_distribution_value_is_rejected():
    engine = DataMimicTest(_dir, "test_distribution_unknown_value.xml", capture_test_result=True)
    with pytest.raises(ValueError, match="(?i)gaussian|distribution"):
        engine.test_with_timer()
