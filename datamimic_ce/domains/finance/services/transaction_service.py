# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Transaction Service.

This module provides utility methods for working with Transaction entities.
"""

from datamimic_ce.domain_core.base_domain_service import BaseDomainService
from datamimic_ce.domains.finance.generators.transaction_generator import TransactionGenerator
from datamimic_ce.domains.finance.models.transaction import Transaction


class TransactionService(BaseDomainService[Transaction]):
    def __init__(self, dataset: str | None = None):
        super().__init__(TransactionGenerator(dataset=dataset), Transaction)
