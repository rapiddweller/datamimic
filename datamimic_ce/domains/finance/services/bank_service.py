# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.domain_core.base_domain_service import BaseDomainService
from datamimic_ce.domains.finance.generators.bank_generator import BankGenerator
from datamimic_ce.domains.finance.models.bank import Bank


class BankService(BaseDomainService[Bank]):
    def __init__(self, dataset: str | None = None):
        super().__init__(BankGenerator(dataset), Bank)
