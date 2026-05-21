# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Patient service.

This module provides the PatientService class for generating and managing patient data.
"""

from datetime import datetime
from random import Random

from datamimic_ce.domains.common.demographics.sampler import DemographicSampler
from datamimic_ce.domains.common.models.demographic_config import DemographicConfig
from datamimic_ce.domains.domain_core import BaseDomainService
from datamimic_ce.domains.domain_core.attribute_catalog import EntitySchema, FieldSpec, field
from datamimic_ce.domains.healthcare.generators.patient_generator import PatientGenerator
from datamimic_ce.domains.healthcare.models.patient import Patient

PATIENT_SCHEMA = EntitySchema(
    "Patient",
    (
        field("patient_id", str, "Unique patient identifier."),
        field("medical_record_number", str, "Medical record number."),
        field("ssn", str, "Social security number."),
        field("given_name", str, "First (given) name."),
        field("family_name", str, "Last (family) name."),
        field("full_name", str, "Full display name."),
        field("gender", str, "Gender."),
        field("birthdate", datetime, "Date of birth."),
        field("age", int, "Age in years."),
        field("blood_type", str, "Blood type."),
        field("height_cm", float, "Height in centimetres."),
        field("weight_kg", float, "Weight in kilograms."),
        field("bmi", float, "Body mass index."),
        field("allergies", list, "Known allergies."),
        field("medications", list, "Current medications."),
        field("conditions", list, "Diagnosed conditions."),
        field("emergency_contact", dict, "Emergency contact details."),
        field("insurance_provider", str, "Insurance provider name."),
        field("insurance_policy_number", str, "Insurance policy number."),
        field("transaction_profile", (str, dict), "Spending/transaction behaviour profile.", optional=True),
        field("primary_doctor", dict, "Primary doctor details (present when assigned)."),
    ),
)


class PatientService(BaseDomainService[Patient]):
    """Service for generating and managing patient data.

    This class provides methods for generating patient data, exporting it to various formats,
    and retrieving patients with specific characteristics.
    """

    def __init__(
        self,
        dataset: str | None = None,
        demographic_config: DemographicConfig | None = None,
        demographic_sampler: DemographicSampler | None = None,
        rng: Random | None = None,
    ):
        # Thread demographic and RNG overrides through the service layer.
        super().__init__(
            PatientGenerator(
                dataset=dataset,
                demographic_config=demographic_config,
                demographic_sampler=demographic_sampler,
                rng=rng,
            ),
            Patient,
        )

    DATASET_PATTERNS = (
        "healthcare/medical/blood_types_{CC}.csv",
        "healthcare/medical/emergency_relationships_{CC}.csv",
        "healthcare/medical/allergies_{CC}.csv",
        "healthcare/medical/medications_{CC}.csv",
        "healthcare/medical/insurance_providers_{CC}.csv",
    )

    @classmethod
    def attribute_specs(cls) -> tuple[FieldSpec, ...]:
        return PATIENT_SCHEMA.fields
