from __future__ import annotations

from pathlib import Path

import pytest

import datamimic_ce.domains as domains_package
from datamimic_ce.domains.domain_core.datasets.path import packaged_domain_data_root
from datamimic_ce.domains.shared.datasets.loader import read_csv_rows

BOM = b"\xef\xbb\xbf"
DOMAINS_ROOT = Path(next(iter(domains_package.__path__)))
FORMERLY_MARKED = (
    "city/city_BR.csv",
    "person/familyName_AT.csv",
    "person/familyName_BR.csv",
    "person/familyName_DE.csv",
    "person/givenName_female_IL.csv",
    "person/givenName_male_CH.csv",
    "person/givenName_male_DE.csv",
    "person/givenName_male_IL.csv",
    "street/street_BR.csv",
    "street/street_DE.csv",
)


def test_no_domain_file_starts_with_a_byte_order_mark() -> None:
    marked = [
        path.relative_to(DOMAINS_ROOT).as_posix()
        for path in sorted(DOMAINS_ROOT.rglob("*"))
        if path.is_file() and path.suffix != ".pyc" and path.read_bytes().startswith(BOM)
    ]

    assert marked == []


@pytest.mark.parametrize("name", FORMERLY_MARKED)
def test_loaded_domain_values_carry_no_zero_width_no_break_space(name: str) -> None:
    path = packaged_domain_data_root() / "common" / name
    delimiter = ";" if path.name == "city_BR.csv" else ","

    rows = read_csv_rows(path, delimiter=delimiter)

    assert rows
    assert [cell for row in rows for cell in row if cell.startswith("﻿")] == []
