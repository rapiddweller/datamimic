# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Insurance Company Coverage Service.

This module provides service functions for generating and managing insurance company coverages.
"""

from random import Random

from datamimic_ce.domains.domain_core import BaseDomainService
from datamimic_ce.domains.insurance.generators.insurance_coverage_generator import InsuranceCoverageGenerator
from datamimic_ce.domains.insurance.models.insurance_coverage import InsuranceCoverage


class InsuranceCoverageService(BaseDomainService[InsuranceCoverage]):
    """Service for generating and managing insurance company coverages."""

    def __init__(self, dataset: str | None = None, rng: Random | None = None):
        super().__init__(InsuranceCoverageGenerator(dataset=dataset, rng=rng), InsuranceCoverage)

    @staticmethod
    def supported_datasets() -> set[str]:
        from pathlib import Path

        from datamimic_ce.domains.utils.supported_datasets import compute_supported_datasets

        return compute_supported_datasets(["insurance/coverages_{CC}.csv"], start=Path(__file__))
