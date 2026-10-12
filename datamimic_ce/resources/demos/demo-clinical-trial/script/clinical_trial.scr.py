from __future__ import annotations

from random import Random

from datamimic_ce.domains.api import DemographicConfig, PatientService


def generate_clinical_cohort() -> list[dict]:
    """Generate a placebo-arm cohort: seniors 70–75 without hypertension.

    Returns a list of dictionaries ready for nestedKey ingestion.
    """
    rng = Random(1337)
    config = DemographicConfig(age_min=70, age_max=75, conditions_exclude=frozenset({"Hypertension"}))
    service = PatientService(dataset="US", demographic_config=config, rng=rng)

    patients = [service.generate() for _ in range(100)]
    rows: list[dict] = []
    for p in patients:
        rows.append(
            {
                "patient_id": p.patient_id,
                "full_name": p.full_name,
                "age": p.age,
                "gender": p.gender,
                "blood_type": p.blood_type,
                "conditions": p.conditions,
            }
        )
    return rows
