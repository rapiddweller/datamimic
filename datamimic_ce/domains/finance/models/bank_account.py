# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Bank Account model.

This module defines the bank account model for the finance domain.
"""

import datetime
import random
from typing import Any

from datamimic_ce.domain_core.base_entity import BaseEntity
from datamimic_ce.domain_core.property_cache import property_cache
from datamimic_ce.domains.finance.generators.bank_account_generator import BankAccountGenerator
from datamimic_ce.domains.finance.models.bank import Bank


class BankAccount(BaseEntity):
    """Bank account information."""

    def __init__(self, bank_account_generator: BankAccountGenerator):
        super().__init__()
        self._bank_account_generator = bank_account_generator

    @property
    @property_cache
    def bank_data(self) -> Bank:
        return Bank(self._bank_account_generator.bank_generator)

    @property
    @property_cache
    def account_number(self) -> str:
        return self._bank_account_generator.account_number_generator.generate()

    @property
    @property_cache
    def iban(self) -> str:
        def checksum(iban_temp):
            tmp = (iban_temp[4:] + iban_temp[0:4]).upper()
            digits = ""
            for c in tmp:
                if "0" <= c <= "9":
                    digits += c
                elif "A" <= c <= "Z":
                    n = ord(c) - ord("A") + 10
                    digits += str(n // 10) + str(n % 10)
                else:
                    return -1
            n = int(digits)
            return n % 97

        template = f"{self._bank_account_generator.dataset.upper()}00{self.bank_code}{self.account_number.zfill(10)}"
        remainer = checksum(template)
        pp = str(98 - remainer).zfill(2)
        return template[:2] + pp + template[4:]

    @property
    @property_cache
    def account_type(self) -> str:
        return self._bank_account_generator.get_bank_account_types()

    @property
    @property_cache
    def balance(self) -> float:
        return random.uniform(0, 1000000)

    @balance.setter
    def balance(self, value: float) -> None:
        """Set the bank account balance.

        Args:
            value: The balance amount to set.
        """
        self._field_cache["balance"] = value

    @property
    @property_cache
    def currency(self) -> str:
        return self._bank_account_generator.get_currency()

    @property
    @property_cache
    def created_date(self) -> datetime.datetime:
        return datetime.datetime.now() - datetime.timedelta(days=random.randint(0, 365))

    @property
    @property_cache
    def last_transaction_date(self) -> datetime.datetime:
        return datetime.datetime.now() - random.uniform(0, 1) * (datetime.datetime.now() - self.created_date)

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

    def to_dict(self) -> dict[str, Any]:
        return {
            "account_number": self.account_number,
            "iban": self.iban,
            "account_type": self.account_type,
            "balance": self.balance,
            "currency": self.currency,
            "created_date": self.created_date,
            "last_transaction_date": self.last_transaction_date,
            "bank_name": self.bank_name,
            "bank_code": self.bank_code,
            "bic": self.bic,
            "bin": self.bin,
        }
