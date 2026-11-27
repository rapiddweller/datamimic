# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

from __future__ import annotations

from pathlib import Path
from random import Random

import pytest

from datamimic_ce.domains.domain_core.base_domain_generator import normalize_dataset
from datamimic_ce.domains.domain_core.datasets.path import dataset_path
from datamimic_ce.domains.shared.datasets.loader import read_weighted_values
from datamimic_ce.domains.shared.generators.address_generator import AddressGenerator
from datamimic_ce.domains.shared.literal_generators.contact import street_name_generator as module
from datamimic_ce.domains.shared.literal_generators.contact.street_name_generator import StreetNameGenerator
from datamimic_ce.domains.shared.models.address import Address


def _street_file(dataset: str) -> Path:
    code = normalize_dataset(dataset)[:2]
    return dataset_path("common", "street", f"street_{code}.csv", start=Path(module.__file__))


def _old_street_names(dataset: str, seed: int, count: int) -> list[str]:
    """The pre-cache behavior: parse the street file again for every address."""
    names = []
    rng = Random(seed)
    for _ in range(count):
        values, weights = read_weighted_values(_street_file(dataset))
        names.append(rng.choices(values, weights, k=1)[0])
    return names


def _new_street_names(dataset: str, seed: int, count: int) -> list[str]:
    rng = Random(seed)
    return [StreetNameGenerator(dataset=dataset, rng=rng).generate() for _ in range(count)]


@pytest.fixture(autouse=True)
def _empty_cache() -> None:
    module._street_files.clear()


# "ZZ" has no street file: the loader falls back to the US file.
@pytest.mark.parametrize("dataset", ["DE", "US", "ZZ"])
def test_seeded_street_names_match_the_uncached_reader(dataset: str) -> None:
    assert _new_street_names(dataset, 7, 25) == _old_street_names(dataset, 7, 25)


@pytest.mark.parametrize("dataset", ["DE", "ZZ"])
def test_each_street_file_is_read_once_for_many_generators(dataset: str, monkeypatch: pytest.MonkeyPatch) -> None:
    reads: list[Path] = []

    def counting_read(path: Path):
        reads.append(path)
        return read_weighted_values(path)

    monkeypatch.setattr(module, "read_weighted_values", counting_read)
    names = [StreetNameGenerator(dataset=dataset).generate() for _ in range(50)]  # unseeded

    assert len(reads) == 1
    assert all(name for name in names)


def test_datasets_do_not_share_cached_rows() -> None:
    de = StreetNameGenerator(dataset="DE", rng=Random(1))
    us = StreetNameGenerator(dataset="US", rng=Random(1))
    assert de._values != us._values
    assert len(module._street_files) == 2


def test_region_group_addresses_match_reference_and_read_each_country_once(monkeypatch: pytest.MonkeyPatch) -> None:
    reads: list[Path] = []

    def counting_read(path: Path):
        reads.append(path)
        return read_weighted_values(path)

    def streets(count: int) -> list[str]:
        rng = Random(11)
        return [Address(AddressGenerator(dataset="europe", rng=rng)).street for _ in range(count)]

    monkeypatch.setattr(module, "read_weighted_values", counting_read)
    first = streets(40)
    assert len(reads) == len(set(reads))  # no file parsed twice
    module._street_files.clear()
    assert streets(40) == first  # seeded replay is identical


def test_edited_file_is_read_again(tmp_path: Path) -> None:
    path = tmp_path / "street_XX.csv"
    path.write_text("Old Road,1\n", encoding="utf-8")
    assert module._load_street_file(path)[0] == ("Old Road",)
    path.write_text("New Avenue,1\nOther Lane,2\n", encoding="utf-8")
    assert module._load_street_file(path)[0] == ("New Avenue", "Other Lane")


def test_missing_file_still_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        module._load_street_file(tmp_path / "street_QQ.csv")
