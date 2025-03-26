# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Transaction model.

This module defines the transaction model for the finance domain.
"""

import datetime
import random
from typing import Any

from datamimic_ce.domain_core.base_entity import BaseEntity
from datamimic_ce.domain_core.property_cache import property_cache
from datamimic_ce.domains.finance.generators.transaction_generator import TransactionGenerator
from datamimic_ce.domains.finance.models.bank_account import BankAccount
from datamimic_ce.utils.data_generation_ce_util import DataGenerationCEUtil


class Transaction(BaseEntity):
    """Financial transaction information."""

    def __init__(self, transaction_generator: TransactionGenerator, bank_account: BankAccount | None = None):
        """Initialize the transaction model.

        Args:
            transaction_generator: Generator for transaction data.
            bank_account: Optional bank account associated with this transaction.
        """
        super().__init__()
        self._transaction_generator = transaction_generator
        self._bank_account = bank_account
        self._merchant_category = self._transaction_generator.get_merchant_category()
        self._transaction_type = self._transaction_generator.get_transaction_type()
        self._transaction_data = self._transaction_generator.generate_transaction_data(bank_account)

        # Generate random transaction date within the last year
        now = datetime.datetime.now()
        days_ago = random.randint(0, 365)
        self._transaction_date = now - datetime.timedelta(days=days_ago)

    @property
    @property_cache
    def transaction_id(self) -> str:
        """Get the unique transaction ID.

        Returns:
            A unique identifier for the transaction.
        """
        return DataGenerationCEUtil.rnd_str_from_regex("[A-Z0-9]{16}")

    @property
    @property_cache
    def account(self) -> BankAccount | None:
        """Get the associated bank account.

        Returns:
            The bank account associated with this transaction, if any.
        """
        return self._bank_account

    @property
    @property_cache
    def transaction_date(self) -> datetime.datetime:
        """Get the transaction date.

        Returns:
            The date and time of the transaction.
        """
        return self._transaction_date

    @property
    @property_cache
    def amount(self) -> float:
        """Get the transaction amount.

        Returns:
            The monetary amount of the transaction.
        """
        return self._transaction_data["amount"]

    @property
    @property_cache
    def transaction_type(self) -> str:
        """Get the transaction type.

        Returns:
            The type of transaction.
        """
        return self._transaction_type["type"]

    @property
    @property_cache
    def description(self) -> str:
        """Get the transaction description.

        Returns:
            A descriptive string for the transaction.
        """
        return self._transaction_data["description"]

    @property
    @property_cache
    def reference_number(self) -> str:
        """Get the transaction reference number.

        Returns:
            A unique reference number for the transaction.
        """
        return self._transaction_data["reference_number"]

    @property
    @property_cache
    def status(self) -> str:
        """Get the transaction status.

        Returns:
            The current status of the transaction.
        """
        return self._transaction_data["status"]

    @property
    @property_cache
    def currency(self) -> str:
        """Get the transaction currency.

        Returns:
            The currency code for the transaction.
        """
        if self._bank_account:
            return self._bank_account.currency

        return self._transaction_data["currency_code"]

    @property
    @property_cache
    def currency_symbol(self) -> str:
        """Get the transaction currency symbol.

        Returns:
            The currency symbol for the transaction.
        """
        return self._transaction_data["currency_symbol"]

    @property
    @property_cache
    def merchant_name(self) -> str:
        """Get the merchant name.

        Returns:
            The name of the merchant involved in the transaction.
        """
        return self._transaction_data["merchant"]

    @property
    @property_cache
    def merchant_category(self) -> str:
        """Get the merchant category.

        Returns:
            The category of the merchant.
        """
        return self._merchant_category

    @property
    @property_cache
    def location(self) -> str:
        """Get the transaction location.

        Returns:
            The location where the transaction occurred.
        """
        return self._transaction_data["location"]

    @property
    @property_cache
    def is_international(self) -> bool:
        """Check if the transaction is international.

        Returns:
            True if the transaction is international, False otherwise.
        """
        return random.choices([True, False], weights=[10, 90], k=1)[0]

    @property
    @property_cache
    def channel(self) -> str:
        """Get the transaction channel.

        Returns:
            The channel through which the transaction was made.
        """
        return self._transaction_data["channel"]

    @property
    @property_cache
    def direction(self) -> str:
        """Get the transaction direction.

        Returns:
            Either 'credit' (money in) or 'debit' (money out).
        """
        return self._transaction_data["direction"]

    def to_dict(self) -> dict[str, Any]:
        """Convert transaction to a dictionary.

        Returns:
            A dictionary representation of the transaction.
        """
        result = {
            "transaction_id": self.transaction_id,
            "transaction_date": self.transaction_date,
            "amount": self.amount,
            "transaction_type": self.transaction_type,
            "description": self.description,
            "reference_number": self.reference_number,
            "status": self.status,
            "currency": self.currency,
            "currency_symbol": self.currency_symbol,
            "merchant_name": self.merchant_name,
            "merchant_category": self.merchant_category,
            "location": self.location,
            "is_international": self.is_international,
            "channel": self.channel,
            "direction": self.direction,
        }

        if self.account:
            result["account"] = {
                "account_number": self.account.account_number,
                "account_type": self.account.account_type,
            }

        return result
