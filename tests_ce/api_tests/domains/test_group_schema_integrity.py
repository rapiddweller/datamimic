"""Schema guard tests for deterministic group datasets."""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

DATASETS = ("US", "DE", "VN")
EXPECTED_COLUMNS = {
    "age_band": ["group_id", "min_age", "max_age", "weight"],
    "condition_prevalence_tier": ["group_id", "condition", "weight"],
    "gender_category": ["group_id", "gender", "weight"],
    "specialty_family": ["group_id", "specialty", "weight"],
    "area_code_cluster": ["group_id", "area_code", "weight"],
    "population_tier": ["group_id", "state_id", "weight"],
    "coverage_line": ["group_id", "product_code", "weight"],
    "sector_macro": ["group_id", "sector", "weight"],
}

BASE_DIR = Path("datamimic_ce/domains/domain_data/groups")


@pytest.mark.parametrize("dimension", sorted(EXPECTED_COLUMNS))
@pytest.mark.parametrize("dataset", DATASETS)
def test_group_schema_matches(dimension: str, dataset: str) -> None:
    path = BASE_DIR / dimension / f"{dimension}_{dataset}.csv"
    assert path.exists(), f"Missing group dataset: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader)
    assert header == EXPECTED_COLUMNS[dimension], f"Unexpected columns in {path}"
