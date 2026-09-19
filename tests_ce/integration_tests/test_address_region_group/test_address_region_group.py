# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""dataset='europe' is a region-group alias: each row independently draws a concrete European
country - AddressGenerator instances are reused across every row of a run (see
generate_worker.py/base_domain_service.py), so resolving the country once in __init__ would give
every row in the run the SAME country, not variety. The draw has to happen per row."""

from pathlib import Path

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest
from datamimic_ce.domains.common.generators.region_groups import REGION_GROUPS

_dir = Path(__file__).resolve().parent


def _run():
    engine = DataMimicTest(test_dir=_dir, filename="address_region_group.xml", capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()


def test_europe_draws_vary_per_row_and_stay_in_the_group():
    result = _run()
    codes = {row["country_code"] for row in result["europe_rows"]}
    assert len(codes) > 1, "dataset='europe' produced the same country for every row"
    assert codes <= set(REGION_GROUPS["EUROPE"])


def test_europe_sub_generators_are_consistent_with_the_drawn_country():
    """city/phone/street must reflect the SAME country_code that was drawn for that row, not a
    stale one left over from AddressGenerator's own (shared, reused) fixed dataset."""
    result = _run()
    for row in result["europe_rows"]:
        assert row["city_country_code"] == row["country_code"]
        assert row["street"]
        assert row["phone"]


def test_single_country_dataset_is_unaffected():
    result = _run()
    assert {row["country_code"] for row in result["de_rows"]} == {"DE"}


def test_europe_is_deterministic_under_a_seed():
    r1, r2 = _run(), _run()
    assert [row["country_code"] for row in r1["europe_rows"]] == [row["country_code"] for row in r2["europe_rows"]]


def test_every_group_code_has_city_and_street_data():
    """Gate: a group member without data files fails only when the seeded draw happens to pick
    it - a flaky runtime crash. Every code in every group must have its city/street CSVs."""
    data_dir = Path(__file__).resolve().parents[3] / "datamimic_ce" / "domains" / "domain_data" / "common"
    for kind in ("city", "street"):
        have = {p.stem.split("_")[-1] for p in (data_dir / kind).glob(f"{kind}_*.csv")}
        for group, codes in REGION_GROUPS.items():
            missing = [c for c in codes if c not in have]
            assert not missing, f"{group} lists codes without {kind} data: {missing}"


def test_subregion_groups_draw_within_their_pool():
    engine = DataMimicTest(test_dir=_dir, filename="subregion_groups.xml", capture_test_result=True)
    engine.test_with_timer()
    result = engine.capture_result()

    iberia_codes = {row["country_code"] for row in result["iberia_rows"]}
    assert iberia_codes <= set(REGION_GROUPS["IBERIA"])
    assert len(iberia_codes) > 1, "dataset='iberia' produced the same country for every row"
    for row in result["iberia_rows"]:
        assert row["city_country_code"] == row["country_code"]

    # uppercase alias resolves like the lowercase one (edge: case-insensitivity)
    assert {row["country_code"] for row in result["upper_rows"]} <= set(REGION_GROUPS["NORTH_AMERICA"])


def test_unknown_dataset_fails_loudly():
    engine = DataMimicTest(test_dir=_dir, filename="unknown_group.xml", capture_test_result=True)
    with pytest.raises(Exception, match="(?i)atlantis"):
        engine.test_with_timer()
