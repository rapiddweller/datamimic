"""Ensure demographic profile metadata references existing deterministic groups."""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

DATASETS = ("US", "DE", "VN")
PROFILE_META_PATTERN = Path("datamimic_ce/domains/domain_data/demographics/profile_meta.dmgrp_{dataset}.csv")
GROUP_DIMENSIONS = {
    "age_group_ref": Path("datamimic_ce/domains/domain_data/groups/age_band/age_band_{dataset}.csv"),
    "gender_group_ref": Path("datamimic_ce/domains/domain_data/groups/gender_category/gender_category_{dataset}.csv"),
    "condition_group_ref": Path("datamimic_ce/domains/domain_data/groups/condition_prevalence_tier/condition_prevalence_tier_{dataset}.csv"),
    "region_group_ref": Path("datamimic_ce/domains/domain_data/groups/population_tier/population_tier_{dataset}.csv"),
    "sector_group_ref": Path("datamimic_ce/domains/domain_data/groups/sector_macro/sector_macro_{dataset}.csv"),
    "specialty_group_ref": Path("datamimic_ce/domains/domain_data/groups/specialty_family/specialty_family_{dataset}.csv"),
    "area_cluster_ref": Path("datamimic_ce/domains/domain_data/groups/area_code_cluster/area_code_cluster_{dataset}.csv"),
    "coverage_line_ref": Path("datamimic_ce/domains/domain_data/groups/coverage_line/coverage_line_{dataset}.csv"),
}


def _load_group_ids(path: Path) -> set[str]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return {row["group_id"] for row in reader}


@pytest.mark.parametrize("dataset", DATASETS)
def test_profile_meta_references_existing_groups(dataset: str) -> None:
    meta_path = Path(str(PROFILE_META_PATTERN).format(dataset=dataset))
    assert meta_path.exists(), f"Missing profile metadata for dataset {dataset}"

    group_cache: dict[str, set[str]] = {}
    with meta_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required_columns = {"dataset", "version", "profile_id"}
        assert required_columns.issubset(reader.fieldnames or []), "profile metadata missing required columns"

        for row in reader:
            assert (row.get("dataset") or "").strip() == dataset, "Dataset mismatch in profile metadata"
            profile_id = (row.get("profile_id") or "").strip()
            assert profile_id, "profile_id must not be empty"

            for column, template in GROUP_DIMENSIONS.items():
                ref_value = (row.get(column) or "").strip()
                if not ref_value:
                    continue
                if column not in group_cache:
                    group_path = Path(str(template).format(dataset=dataset))
                    assert group_path.exists(), f"Missing group table for {column} ({dataset})"
                    group_cache[column] = _load_group_ids(group_path)
                assert (
                    ref_value in group_cache[column]
                ), f"Unknown group id '{ref_value}' for column '{column}' (dataset {dataset})"
