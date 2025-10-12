"""Integration test for building a sampler with profile metadata group refs applied."""

from __future__ import annotations

from pathlib import Path

import pytest

from datamimic_ce.domains.common.demographics import build_sampler_with_profile_groups


@pytest.fixture()
def demo_profile_dir(tmp_path: Path) -> Path:
    # Create minimal demographic CSVs for dataset US/v1
    (tmp_path / "age_pyramid.dmgrp.csv").write_text(
        """
dataset,version,sex,age_min,age_max,weight
US,v1,F,0,17,0.3
US,v1,F,18,44,0.5
US,v1,F,45,90,0.2
US,v1,M,0,17,0.3
US,v1,M,18,44,0.5
US,v1,M,45,90,0.2
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "condition_rates.dmgrp.csv").write_text(
        """
dataset,version,condition,sex,age_min,age_max,prevalence
US,v1,Hypertension,,0,120,0.2
US,v1,Type 2 Diabetes,,0,120,0.15
""".strip()
        + "\n",
        encoding="utf-8",
    )
    return tmp_path


def test_build_sampler_with_profile_groups_applies_masks(demo_profile_dir: Path) -> None:
    sampler = build_sampler_with_profile_groups(
        directory=demo_profile_dir,
        dataset="US",
        version="v1",
        profile_id="urban_adult",
        request_hash="it",
    )

    # The integration should apply at least one group mask from metadata.
    # Gender mask is well-formed across keys in repo data (age mask may be rejected in non-strict mode
    # if bounds are violated by single-band groups), so assert on gender.
    gender_mask = sampler.group_mask("gender_category")
    assert gender_mask, "Expected gender_category mask to be applied from profile metadata"
    # Provenance must track group file usage
    assert sampler.provenance_hash(), "Expected provenance to be recorded for applied group tables"
