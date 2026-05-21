# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import datetime as dt
import random
from datetime import datetime

from datamimic_ce.domains.domain_core import BaseDomainService
from datamimic_ce.domains.domain_core.attribute_catalog import EntitySchema, FieldSpec, field
from datamimic_ce.domains.finance.generators.bank_account_generator import BankAccountGenerator
from datamimic_ce.domains.finance.models.bank_account import BankAccount

BANK_ACCOUNT_SCHEMA = EntitySchema(
    "BankAccount",
    (
        field("account_number", str, "Account number."),
        field("iban", str, "International bank account number."),
        field("account_type", str, "Account type."),
        field("balance", float, "Current account balance."),
        field("currency", str, "Account currency code."),
        field("created_date", datetime, "Account creation date."),
        field("last_transaction_date", datetime, "Date of the last transaction."),
        field("bank_name", str, "Bank name."),
        field("bank_code", str, "Bank code."),
        field("bic", str, "Bank identifier code (BIC)."),
        field("bin", str, "Bank identification number (BIN)."),
    ),
)


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
    def attribute_specs(cls) -> tuple[FieldSpec, ...]:
        return BANK_ACCOUNT_SCHEMA.fields

    @staticmethod
    def supported_datasets() -> set[str]:
        from pathlib import Path

        from datamimic_ce.domains.utils.supported_datasets import compute_supported_datasets

        patterns = [
            "finance/account_types_{CC}.csv",
            "ecommerce/currencies_{CC}.csv",
        ]
        return compute_supported_datasets(patterns, start=Path(__file__))
