"""
Use case: Rare disease registry requires presence of 'fabry' at least once.
- conditions_include={'fabry'}
Expected: 'fabry' appears ≥1 time across 1000 samples; no timeouts.
"""

import random

from datamimic_ce.domains.common.models.demographic_config import DemographicConfig
from datamimic_ce.domains.healthcare.services.patient_service import PatientService
from datamimic_ce.domains.healthcare.generators import patient_generator


def test_including_rare_condition_appears_eventually(monkeypatch) -> None:
    # Monkeypatch base weights to include 'fabry' without touching domain_data
    monkeypatch.setattr(
        patient_generator,
        "_load_condition_base_weights",
        lambda dataset: {"diabetes": 1.0, "hypertension": 1.0, "fabry": 0.05},
    )

    rng = random.Random(1337)
    config = DemographicConfig(conditions_include=frozenset({"fabry"}))
    service = PatientService(dataset="US", demographic_config=config, rng=rng)

    patients = [service.generate() for _ in range(1000)]
    assert any(
        any("fabry" in condition.lower() for condition in patient.conditions)
        for patient in patients
    )
