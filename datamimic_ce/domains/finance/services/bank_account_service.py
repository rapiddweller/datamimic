# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import datetime as dt
import random

from datamimic_ce.domains.domain_core import BaseDomainService
from datamimic_ce.domains.domain_core.attribute_catalog import AttributeSpec, specs
from datamimic_ce.domains.finance.generators.bank_account_generator import BankAccountGenerator
from datamimic_ce.domains.finance.models.bank_account import BankAccount


class BankAccountService(BaseDomainService[BankAccount]):
    def __init__(
        self,
        dataset: str | None = None,
        rng: random.Random | None = None,
        reference_now: dt.datetime | None = None,
    ):
        super().__init__(
            BankAccountGenerator(dataset=dataset, rng=rng, reference_now=reference_now),
            BankAccount,
        )

    @classmethod
    def attribute_specs(cls) -> tuple[AttributeSpec, ...]:
        return specs(
            ("account_number", "str", "Account number."),
            ("iban", "str", "International bank account number."),
            ("account_type", "str", "Account type."),
            ("balance", "float", "Current account balance."),
            ("currency", "str", "Account currency code."),
            ("created_date", "datetime", "Account creation date."),
            ("last_transaction_date", "datetime", "Date of the last transaction."),
            ("bank_name", "str", "Bank name."),
            ("bank_code", "str", "Bank code."),
            ("bic", "str", "Bank identifier code (BIC)."),
            ("bin", "str", "Bank identification number (BIN)."),
        )

    @staticmethod
    def supported_datasets() -> set[str]:
        from pathlib import Path

        from datamimic_ce.domains.utils.supported_datasets import compute_supported_datasets

        patterns = [
            "finance/account_types_{CC}.csv",
            "ecommerce/currencies_{CC}.csv",
        ]
        return compute_supported_datasets(patterns, start=Path(__file__))
