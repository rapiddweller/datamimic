import csv
from pathlib import Path
from random import Random

import datamimic_ce
from datamimic_ce.domains.shared.generators.address_generator import AddressGenerator
from datamimic_ce.domains.shared.models.address import Address

CITY_DE = Path(datamimic_ce.__file__).parent / "domains/shared/domain_data/common/city/city_DE.csv"


def test_generated_de_postal_code_and_city_are_one_row_of_the_city_data() -> None:
    with CITY_DE.open(encoding="utf-8-sig", newline="") as source:
        rows = {(str(row["postalCode"]), row["name"]) for row in csv.DictReader(source, delimiter=";")}
    rng = Random(7)

    pairs = [(a.postal_code, a.city) for a in (Address(AddressGenerator(dataset="DE", rng=rng)) for _ in range(200))]

    assert [pair for pair in pairs if pair not in rows] == []
