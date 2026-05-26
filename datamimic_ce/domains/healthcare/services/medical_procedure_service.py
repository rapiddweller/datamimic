# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Medical Procedure service.

This module provides the MedicalProcedureService class for generating and managing medical procedure data.
"""

from random import Random

from datamimic_ce.domains.domain_core import BaseDomainService
from datamimic_ce.domains.domain_core.attribute_catalog import EntitySchema, FieldSpec, field
from datamimic_ce.domains.healthcare.generators.medical_procedure_generator import MedicalProcedureGenerator
from datamimic_ce.domains.healthcare.models.medical_procedure import MedicalProcedure

MEDICAL_PROCEDURE_SCHEMA = EntitySchema(
    "MedicalProcedure",
    (
        field("procedure_id", str, "Unique procedure identifier."),
        field("procedure_code", str, "Internal procedure code."),
        field("cpt_code", str, "CPT billing code."),
        field("name", str, "Procedure name."),
        field("description", str, "Procedure description."),
        field("category", str, "Procedure category."),
        field("specialty", str, "Associated medical specialty."),
        field("duration_minutes", int, "Typical duration in minutes."),
        field("cost", float, "Procedure cost."),
        field("requires_anesthesia", bool, "Whether anesthesia is required."),
        field("is_surgical", bool, "Whether the procedure is surgical."),
        field("is_diagnostic", bool, "Whether the procedure is diagnostic."),
        field("is_preventive", bool, "Whether the procedure is preventive."),
        field("recovery_time_days", int, "Typical recovery time in days."),
    ),
)


class MedicalProcedureService(BaseDomainService[MedicalProcedure]):
    """Service for generating and managing medical procedure data.

    This class provides methods for generating medical procedure data, exporting it to various formats,
    and retrieving procedures with specific characteristics.
    """

    def __init__(self, dataset: str | None = None, rng: Random | None = None):
        super().__init__(MedicalProcedureGenerator(dataset=dataset, rng=rng), MedicalProcedure)

    DATASET_PATTERNS = (
        "healthcare/medical/procedure_name_patterns_{CC}.csv",
        "healthcare/medical/specialties_{CC}.csv",
        "healthcare/medical/procedure_categories_{CC}.csv",
    )

    @classmethod
    def attribute_specs(cls) -> tuple[FieldSpec, ...]:
        return MEDICAL_PROCEDURE_SCHEMA.fields
