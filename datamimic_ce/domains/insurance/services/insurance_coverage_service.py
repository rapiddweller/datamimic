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
from datamimic_ce.domains.domain_core.attribute_catalog import EntitySchema, FieldSpec, field
from datamimic_ce.domains.insurance.generators.insurance_coverage_generator import InsuranceCoverageGenerator
from datamimic_ce.domains.insurance.models.insurance_coverage import InsuranceCoverage

INSURANCE_COVERAGE_SCHEMA = EntitySchema(
    "InsuranceCoverage",
    (
        field("name", str, "Coverage name."),
        field("code", str, "Coverage code."),
        field("product_code", str, "Associated product code."),
        field("description", str, "Coverage description."),
        field("min_coverage", str, "Minimum coverage amount."),
        field("max_coverage", str, "Maximum coverage amount."),
    ),
)


class InsuranceCoverageService(BaseDomainService[InsuranceCoverage]):
    """Service for generating and managing insurance company coverages."""

    def __init__(self, dataset: str | None = None, rng: Random | None = None):
        super().__init__(
            InsuranceCoverageGenerator(dataset=dataset, rng=rng), InsuranceCoverage
        )

    DATASET_PATTERNS = ("insurance/coverages_{CC}.csv",)

    @classmethod
    def attribute_specs(cls) -> tuple[FieldSpec, ...]:
        return INSURANCE_COVERAGE_SCHEMA.fields
