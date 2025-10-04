# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.domains.domain_core import BaseDomainService
from datamimic_ce.domains.finance.generators.bank_account_generator import BankAccountGenerator
from datamimic_ce.domains.finance.models.bank_account import BankAccount


class BankAccountService(BaseDomainService[BankAccount]):
    def __init__(self, dataset: str | None = None):
        super().__init__(BankAccountGenerator(dataset=dataset), BankAccount)

    @staticmethod
    def supported_datasets() -> set[str]:
        from pathlib import Path

        from datamimic_ce.domains.utils.supported_datasets import compute_supported_datasets

        patterns = [
            "finance/account_types_{CC}.csv",
            "ecommerce/currencies_{CC}.csv",
        ]
        return compute_supported_datasets(patterns, start=Path(__file__))
