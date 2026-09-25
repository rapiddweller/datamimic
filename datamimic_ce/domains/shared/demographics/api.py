"""Convenience API for building a demographic sampler with metadata-applied groups.

Provide a simple integration that loads a demographic profile and applies
group references from profile metadata in one call, so callers don't have to
manually stitch loader + profile_meta + sampler wiring.
"""

from __future__ import annotations

from pathlib import Path

from .loader import load_demographic_profile
from .profile_meta import profile_group_refs
from .sampler import DemographicSampler


def build_sampler_with_profile_groups(
    *,
    directory: Path,
    dataset: str,
    version: str,
    profile_id: str,
    request_hash: str,
) -> DemographicSampler:
    """Load profile CSVs and return a sampler with profile group masks applied.

    Parameters
    - directory: Folder containing age_pyramid.dmgrp.csv and condition_rates.dmgrp.csv
    - dataset: Dataset code matching the CSV rows (e.g., "US")
    - version: Profile version (e.g., "v1")
    - profile_id: Profile metadata row id to look up group refs
    - request_hash: Hash or identifier for error context tracking
    """

    # Load the core demographic profile (pure domain model)
    profile = load_demographic_profile(directory, dataset, version)
    sampler = DemographicSampler(profile)

    # Apply group references from profile metadata if available
    refs = profile_group_refs(
        dataset=dataset,
        version=version,
        profile_id=profile_id,
        request_hash=request_hash,
    )
    if refs:
        sampler.apply_profile_groups(refs, dataset, version)
    return sampler
