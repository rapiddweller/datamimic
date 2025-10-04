"""
Use case: Clinical trial placebo arm needs seniors 70–75 without hypertension.
- Constrain age range to [70,75].
- Exclude 'hypertension'.
Expected:
- All generated ages in [70,75].
- 'hypertension' never appears.
"""

import random

from datamimic_ce.domains.common.models.demographic_config import DemographicConfig
from datamimic_ce.domains.healthcare.services.patient_service import PatientService


def test_patient_age_bounds_and_excluded_condition() -> None:
    rng = random.Random(1337)
    config = DemographicConfig(age_min=70, age_max=75, conditions_exclude=frozenset({"Hypertension"}))
    service = PatientService(demographic_config=config, rng=rng)

    patients = [service.generate() for _ in range(300)]

    for patient in patients:
        assert 70 <= patient.age <= 75
        assert all("hypertension" not in condition.lower() for condition in patient.conditions)
