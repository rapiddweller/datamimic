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
