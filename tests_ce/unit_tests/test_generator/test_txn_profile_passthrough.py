"""
Use case: Student profile should pass a 'student' transaction_profile downstream.
- Only verifying passthrough (no finance rework here).
Expected: patient/person record exposes transaction_profile='student' (or attached config).
"""

import random

from datamimic_ce.domains.common.models.demographic_config import DemographicConfig
from datamimic_ce.domains.common.services.person_service import PersonService
from datamimic_ce.domains.healthcare.services.patient_service import PatientService


def test_transaction_profile_passthrough_to_entities() -> None:
    rng = random.Random(2024)
    config = DemographicConfig(transaction_profile="student")

    person = PersonService(demographic_config=config, rng=rng).generate()
    assert person.transaction_profile == "student"

    patient = PatientService(demographic_config=config, rng=rng).generate()
    assert patient.transaction_profile == "student"
