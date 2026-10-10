"""Demographic profile domain package."""

from .api import build_sampler_with_profile_groups
from .loader import DemographicProfileError, load_demographic_profile
from .profile import DemographicProfile, DemographicProfileId, normalize_sex
from .profile_meta import profile_group_refs
from .sampler import DemographicSample, DemographicSampler

__all__ = [
    "DemographicProfile",
    "DemographicProfileId",
    "DemographicProfileError",
    "DemographicSampler",
    "DemographicSample",
    "load_demographic_profile",
    "normalize_sex",
    "profile_group_refs",
    "build_sampler_with_profile_groups",
]
