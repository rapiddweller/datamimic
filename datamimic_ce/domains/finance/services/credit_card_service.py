# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.domain_core.base_domain_service import BaseDomainService
from datamimic_ce.domains.finance.generators.credit_card_generator import CreditCardGenerator
from datamimic_ce.domains.finance.models.credit_card import CreditCard


class CreditCardService(BaseDomainService[CreditCard]):
    def __init__(self, dataset: str | None = None):
        super().__init__(CreditCardGenerator(dataset=dataset), CreditCard)
