# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random

from datamimic_ce.domains.domain_core import BaseDomainService
from datamimic_ce.domains.domain_core.attribute_catalog import AttributeSpec, specs
from datamimic_ce.domains.finance.generators.bank_generator import BankGenerator
from datamimic_ce.domains.finance.models.bank import Bank


class BankService(BaseDomainService[Bank]):
    def __init__(self, dataset: str | None = None, rng: random.Random | None = None):
        super().__init__(BankGenerator(dataset, rng=rng), Bank)

    @classmethod
    def attribute_specs(cls) -> tuple[AttributeSpec, ...]:
        return specs(
            ("name", "str", "Bank name."),
            ("swift_code", "str", "SWIFT code."),
            ("routing_number", "str", "Routing number."),
            ("bank_code", "str", "Bank code."),
            ("bic", "str", "Bank identifier code (BIC)."),
            ("bin", "str", "Bank identification number (BIN)."),
            ("customer_service_phone", "str", "Customer service phone number."),
        )

    @staticmethod
    def supported_datasets() -> set[str]:
        from pathlib import Path

        from datamimic_ce.domains.utils.supported_datasets import compute_supported_datasets

        return compute_supported_datasets(["finance/bank/banks_{CC}.csv"], start=Path(__file__))
