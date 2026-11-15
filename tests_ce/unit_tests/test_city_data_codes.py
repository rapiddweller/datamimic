from __future__ import annotations

from pathlib import Path
from random import Random

import pytest

from datamimic_ce.domains.domain_core.datasets.path import packaged_domain_data_root
from datamimic_ce.domains.shared.datasets.loader import read_headered_csv
from datamimic_ce.domains.shared.generators.address_generator import AddressGenerator
from datamimic_ce.domains.shared.models.address import Address

CITY_DIR = packaged_domain_data_root() / "common" / "city"
CITY_FILES = sorted(CITY_DIR.glob("city_*.csv"))
FIVE_DIGIT_COUNTRIES = ("US", "DE")
# The leading 0 belongs to the number in these countries; elsewhere areaCode omits the trunk prefix.
AREA_CODE_WITH_LEADING_ZERO = {"IT", "SM", "VA"}
LEADING_ZERO_STATES = {"US": "NJ", "DE": "SN"}


def _column(path: Path, name: str) -> list[str]:
    header, rows = read_headered_csv(path, delimiter=";")
    keys = {key.strip('"﻿'): index for key, index in header.items()}
    return [row[keys[name]] for row in rows] if name in keys else []


@pytest.mark.parametrize("country", FIVE_DIGIT_COUNTRIES)
def test_postal_codes_keep_five_digits_with_their_leading_zero(country: str) -> None:
    codes = _column(CITY_DIR / f"city_{country}.csv", "postalCode")

    assert codes
    assert [code for code in codes if not (len(code) == 5 and code.isdigit())] == []


@pytest.mark.parametrize("path", CITY_FILES, ids=lambda path: path.stem)
def test_area_codes_omit_the_trunk_prefix_except_where_zero_is_part_of_the_number(path: Path) -> None:
    country = path.stem.removeprefix("city_")
    leading_zero = [code for code in _column(path, "areaCode") if code.startswith("0")]

    assert bool(leading_zero) == (country in AREA_CODE_WITH_LEADING_ZERO)


def test_us_city_names_do_not_end_in_a_lowercase_city() -> None:
    names = _column(CITY_DIR / "city_US.csv", "name")

    assert [name for name in names if name.endswith(" city")] == []


@pytest.mark.parametrize("country", FIVE_DIGIT_COUNTRIES)
def test_seeded_address_in_a_leading_zero_state_has_a_five_digit_postal_code(country: str) -> None:
    addresses = [Address(AddressGenerator(dataset=country, rng=Random(seed))) for seed in range(300)]
    in_state = [address for address in addresses if address.state == LEADING_ZERO_STATES[country]]

    assert in_state
    assert all(len(address.postal_code) == 5 for address in addresses)
    assert any(address.postal_code.startswith("0") for address in in_state)
