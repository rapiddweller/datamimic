# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Transaction Service.

This module provides utility methods for working with Transaction entities.
"""

from datetime import datetime
from random import Random

from datamimic_ce.domains.domain_core import BaseDomainService
from datamimic_ce.domains.domain_core.attribute_catalog import EntitySchema, FieldSpec, field, group
from datamimic_ce.domains.finance.generators.transaction_generator import TransactionGenerator
from datamimic_ce.domains.finance.models.transaction import Transaction

TRANSACTION_SCHEMA = EntitySchema(
    "Transaction",
    (
        field("transaction_id", str, "Unique transaction identifier."),
        field("transaction_date", datetime, "Date and time of the transaction."),
        field("amount", float, "Transaction amount."),
        field("transaction_type", str, "Transaction type."),
        field("description", str, "Transaction description."),
        field("reference_number", str, "Reference number."),
        field("status", str, "Transaction status."),
        field("currency", str, "Currency code."),
        field("currency_symbol", str, "Currency symbol."),
        field("merchant_name", str, "Merchant name."),
        field("merchant_category", str, "Merchant category."),
        field("location", str, "Transaction location."),
        field("is_international", bool, "Whether the transaction is international."),
        field("channel", str, "Transaction channel."),
        field("direction", str, "Transaction direction (debit/credit)."),
        group(
            "account",
            "Associated account summary (present when an account is linked).",
            (
                field("account_number", str, "Account number."),
                field("account_type", str, "Account type."),
            ),
            optional=True,
        ),
    ),
)


class TransactionService(BaseDomainService[Transaction]):
    DATASET_PATTERNS = (
        "finance/transaction/transaction_types_{CC}.csv",
        "finance/transaction/categories_{CC}.csv",
        "finance/transaction/merchants_{CC}.csv",
        "finance/transaction/description_templates_{CC}.csv",
        "finance/transaction/amount_ranges_{CC}.csv",
        "finance/transaction/transaction_type_modifiers_{CC}.csv",
        "finance/transaction/status_{CC}.csv",
        "finance/transaction/channels_{CC}.csv",
        "finance/transaction/currency_mapping_{CC}.csv",
        # City dataset lives under common; needed for location generation
        "common/city/city_{CC}.csv",
        # Currencies are shared in ecommerce; used for symbol lookup
        "ecommerce/currencies_{CC}.csv",
    )

    def __init__(
        self,
        dataset: str | None = None,
        rng: Random | None = None,
        reference_now: datetime | None = None,
    ):
        super().__init__(
            TransactionGenerator(dataset=dataset, rng=rng, reference_now=reference_now),
            Transaction,
        )

    @classmethod
    def attribute_specs(cls) -> tuple[FieldSpec, ...]:
        return TRANSACTION_SCHEMA.fields
