# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random

from datamimic_ce.domains.domain_core import BaseDomainService
from datamimic_ce.domains.domain_core.attribute_catalog import EntitySchema, FieldSpec, field
from datamimic_ce.domains.finance.generators.bank_generator import BankGenerator
from datamimic_ce.domains.finance.models.bank import Bank

BANK_SCHEMA = EntitySchema(
    "Bank",
    (
        field("name", str, "Bank name."),
        field("swift_code", str, "SWIFT code."),
        field("routing_number", str, "Routing number."),
        field("bank_code", str, "Bank code."),
        field("bic", str, "Bank identifier code (BIC)."),
        field("bin", str, "Bank identification number (BIN)."),
        field("customer_service_phone", str, "Customer service phone number."),
    ),
)


class BankService(BaseDomainService[Bank]):
    def __init__(self, dataset: str | None = None, rng: random.Random | None = None):
        super().__init__(BankGenerator(dataset, rng=rng), Bank)

    @classmethod
    def attribute_specs(cls) -> tuple[FieldSpec, ...]:
        return BANK_SCHEMA.fields

    @staticmethod
    def supported_datasets() -> set[str]:
        from pathlib import Path

        from datamimic_ce.domains.utils.supported_datasets import compute_supported_datasets

        return compute_supported_datasets(["finance/bank/banks_{CC}.csv"], start=Path(__file__))
