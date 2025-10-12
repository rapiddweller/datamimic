"""Validate that group masks remain normalized for demographic profiles."""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import pytest

DATASETS = ("US", "DE", "VN")
GROUP_DIRS = {
    "age_band": Path("datamimic_ce/domains/domain_data/groups/age_band"),
    "condition_prevalence_tier": Path("datamimic_ce/domains/domain_data/groups/condition_prevalence_tier"),
    "gender_category": Path("datamimic_ce/domains/domain_data/groups/gender_category"),
    "specialty_family": Path("datamimic_ce/domains/domain_data/groups/specialty_family"),
    "area_code_cluster": Path("datamimic_ce/domains/domain_data/groups/area_code_cluster"),
    "population_tier": Path("datamimic_ce/domains/domain_data/groups/population_tier"),
    "coverage_line": Path("datamimic_ce/domains/domain_data/groups/coverage_line"),
    "sector_macro": Path("datamimic_ce/domains/domain_data/groups/sector_macro"),
}

TOLERANCE = 1e-3


def _load_group_sums(dim: str, dataset: str) -> dict[str, float]:
    path = GROUP_DIRS[dim] / f"{dim}_{dataset}.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        sums: dict[str, float] = defaultdict(float)
        for row in reader:
            sums[row["group_id"]] += float(row["weight"])
    return sums


@pytest.mark.parametrize("dataset", DATASETS)
def test_group_weights_normalized(dataset: str) -> None:
    for dim in GROUP_DIRS:
        sums = _load_group_sums(dim, dataset)
        assert sums, f"No rows found for {dim} ({dataset})"
        total_mass = sum(sums.values())
        assert abs(total_mass - 1.0) <= TOLERANCE, f"{dim}_{dataset} weights do not sum to 1 (sum={total_mass})"
        for group_id, total in sums.items():
            assert total > 0.0, f"Group {group_id} in {dim}_{dataset} has zero weight"
