# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Credit Card model.

This module defines the credit card model for the finance domain.
"""

from datetime import datetime

from datamimic_ce.domains.domain_core import BaseEntity
from datamimic_ce.domains.domain_core.property_cache import property_cache
from datamimic_ce.domains.finance.generators.credit_card_generator import CreditCardGenerator
from datamimic_ce.domains.finance.models.bank import Bank
from datamimic_ce.domains.finance.models.bank_account import BankAccount
from datamimic_ce.domains.shared.models.person import Person


class CreditCard(BaseEntity):
    def __init__(self, credit_card_generator: CreditCardGenerator):
        super().__init__()
        self._credit_card_generator = credit_card_generator

    @property
    @property_cache
    def card_holder_data(self) -> Person:
        return Person(self._credit_card_generator.person_generator)

    @property
    @property_cache
    def bank_account_data(self) -> BankAccount:
        return BankAccount(self._credit_card_generator.bank_account_generator)

    @property
    @property_cache
    def bank_data(self) -> Bank:
        return self.bank_account_data.bank_data

    @property
    @property_cache
    def card_type(self) -> str:
        return self._credit_card_generator.generate_card_type()

    @property
    @property_cache
    def card_number(self) -> str:
        return self._credit_card_generator.generate_card_number()

    @property
    @property_cache
    def card_provider(self) -> str:
        return self.bank_data.name

    @property
    @property_cache
    def card_holder(self) -> str:
        return self.card_holder_data.name

    @property
    @property_cache
    def expiration_date(self) -> datetime | str:
        return self._credit_card_generator.date_generator.generate()

    @property
    @property_cache
    def cvv(self) -> str:
        return self._credit_card_generator.generate_security_code()

    @property
    @property_cache
    def cvc_number(self) -> str:
        return self._credit_card_generator.generate_security_code()

    @property
    @property_cache
    def is_active(self) -> bool:
        return self._credit_card_generator.generate_is_active()

    @property
    @property_cache
    def credit_limit(self) -> float:
        return self._credit_card_generator.generate_credit_limit()

    @property
    @property_cache
    def current_balance(self) -> float:
        return self._credit_card_generator.generate_current_balance()

    @property
    @property_cache
    def issue_date(self) -> datetime | str:
        return self._credit_card_generator.date_generator.generate()

    @property
    @property_cache
    def bank_name(self) -> str:
        return self.bank_data.name

    @property
    @property_cache
    def bank_code(self) -> str:
        return self.bank_data.bank_code

    @property
    @property_cache
    def bic(self) -> str:
        return self.bank_data.bic

    @property
    @property_cache
    def bin(self) -> str:
        return self.bank_data.bin

    @property
    @property_cache
    def iban(self) -> str:
        return self.bank_account_data.iban

    def to_dict(self) -> dict[str, object]:
        return {
            "card_type": self.card_type,
            "card_number": self.card_number,
            "card_provider": self.card_provider,
            "card_holder": self.card_holder,
            "expiration_date": self.expiration_date,
            "cvv": self.cvv,
            "cvc_number": self.cvc_number,
            "is_active": self.is_active,
            "credit_limit": self.credit_limit,
            "current_balance": self.current_balance,
            "issue_date": self.issue_date,
            "bank_name": self.bank_name,
            "bank_code": self.bank_code,
            "bic": self.bic,
            "bin": self.bin,
            "iban": self.iban,
        }
