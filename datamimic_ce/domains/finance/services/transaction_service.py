# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Transaction Service.

This module provides utility methods for working with Transaction entities.
"""

from datamimic_ce.domains.domain_core import BaseDomainService
from datamimic_ce.domains.finance.generators.transaction_generator import TransactionGenerator
from datamimic_ce.domains.finance.models.transaction import Transaction


class TransactionService(BaseDomainService[Transaction]):
    def __init__(self, dataset: str | None = None):
        super().__init__(TransactionGenerator(dataset=dataset), Transaction)

    @staticmethod
    def supported_datasets() -> set[str]:
        from pathlib import Path

        from datamimic_ce.domains.utils.supported_datasets import compute_supported_datasets

        patterns = [
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
        ]
        return compute_supported_datasets(patterns, start=Path(__file__))
