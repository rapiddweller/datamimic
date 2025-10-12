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
from datamimic_ce.domains.healthcare.generators.medical_procedure_generator import MedicalProcedureGenerator
from datamimic_ce.domains.healthcare.models.medical_procedure import MedicalProcedure


class MedicalProcedureService(BaseDomainService[MedicalProcedure]):
    """Service for generating and managing medical procedure data.

    This class provides methods for generating medical procedure data, exporting it to various formats,
    and retrieving procedures with specific characteristics.
    """

    def __init__(self, dataset: str | None = None, rng: Random | None = None):
        super().__init__(MedicalProcedureGenerator(dataset=dataset, rng=rng), MedicalProcedure)

    @staticmethod
    def supported_datasets() -> set[str]:
        from pathlib import Path

        from datamimic_ce.domains.utils.supported_datasets import compute_supported_datasets

        patterns = [
            "healthcare/medical/procedure_name_patterns_{CC}.csv",
            "healthcare/medical/specialties_{CC}.csv",
            "healthcare/medical/procedure_categories_{CC}.csv",
        ]
        return compute_supported_datasets(patterns, start=Path(__file__))
