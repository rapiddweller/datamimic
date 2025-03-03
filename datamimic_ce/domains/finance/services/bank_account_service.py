# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Bank Account Service.

This module provides service functions for generating and managing bank accounts.
"""

import random
import uuid
from datetime import datetime, timedelta

from datamimic_ce.domains.finance.data_loaders.bank_loader import BankDataLoader
from datamimic_ce.domains.finance.models.bank_account import Bank, BankAccount
from datamimic_ce.domains.finance.utils.validation_utils import generate_us_routing_number
from datamimic_ce.entities.bank_account_entity import create_iban


class BankAccountService:
    """Service for generating and managing bank accounts."""

    def __init__(self, dataset: str = "US"):
        """Initialize the bank account service.

        Args:
            dataset: The country code (e.g., "US", "DE") to use for data generation.
        """
        self.dataset = dataset
        # Cache the loaded banks
        self._banks_by_weight = BankDataLoader._load_banks_by_weight(dataset)
        self._account_types = BankDataLoader.load_account_types(dataset)

    def generate_bank(self) -> Bank:
        """Generate a random bank based on weighted probabilities.

        Returns:
            A Bank object with randomly generated data.
        """
        if not self._banks_by_weight:
            raise ValueError(f"No banks found for dataset {self.dataset}")

        # Select a bank based on weights
        banks = [b[0] for b in self._banks_by_weight]
        weights = [b[1] for b in self._banks_by_weight]

        selected_bank = random.choices(banks, weights=weights, k=1)[0]

        # Create and return a Bank object
        routing_number = selected_bank.get("routing_number")

        # Generate a routing number if one is not provided and we're in the US
        if not routing_number and self.dataset == "US":
            routing_number = generate_us_routing_number()

        return Bank(
            name=selected_bank.get("name", "Unknown Bank"),
            swift_code=selected_bank.get("swift_code", ""),
            routing_number=routing_number,
        )

    def generate_account_number(self) -> str:
        """Generate a random account number.

        Returns:
            A randomly generated account number.
        """
        # Length depends on country
        if self.dataset == "DE":
            length = 10
        else:  # Default to US
            length = 9

        # Generate a random account number of the specified length
        return "".join([str(random.randint(0, 9)) for _ in range(length)])

    def generate_account_type(self) -> str:
        """Generate a random account type based on weighted probabilities.

        Returns:
            A randomly selected account type.
        """
        if not self._account_types:
            raise ValueError(f"No account types found for dataset {self.dataset}")

        account_types = [t[0] for t in self._account_types]
        weights = [t[1] for t in self._account_types]

        return random.choices(account_types, weights=weights, k=1)[0]

    def generate_iban(self, bank: Bank, account_number: str) -> str | None:
        """Generate an IBAN for the given bank and account number.

        Args:
            bank: The bank for which to generate the IBAN
            account_number: The account number to use in the IBAN

        Returns:
            An IBAN string, or None if the dataset doesn't use IBANs
        """
        if self.dataset in ["DE", "FR", "ES", "IT", "NL"]:
            return create_iban(self.dataset, bank.swift_code[:8], account_number)
        return None

    def generate_bank_account(
        self,
        bank: Bank | None = None,
        account_number: str | None = None,
        account_type: str | None = None,
        balance: float | None = None,
        currency: str | None = None,
    ) -> BankAccount:
        """Generate a random bank account.

        Args:
            bank: Optional predefined bank to use
            account_number: Optional predefined account number to use
            account_type: Optional predefined account type to use
            balance: Optional predefined balance to use
            currency: Optional predefined currency to use

        Returns:
            A BankAccount object with randomly generated data.
        """
        # Generate values for any parameters not provided
        if bank is None:
            bank = self.generate_bank()

        if account_number is None:
            account_number = self.generate_account_number()

        if account_type is None:
            account_type = self.generate_account_type()

        if balance is None:
            # Generate a random balance between 0 and 10000
            balance = round(random.uniform(0, 10000), 2)

        if currency is None:
            if self.dataset == "US":
                currency = "USD"
            elif self.dataset == "DE":
                currency = "EUR"
            else:
                currency = "USD"

        # Generate a created date between 1 and 5 years ago
        days_ago = random.randint(365, 365 * 5)
        created_date = datetime.now() - timedelta(days=days_ago)

        # Generate a last transaction date that's more recent than the created date
        last_transaction_days_ago = random.randint(0, days_ago - 1)
        last_transaction_date = datetime.now() - timedelta(days=last_transaction_days_ago)

        # Generate the IBAN if needed
        iban = self.generate_iban(bank, account_number)

        # Create and return a BankAccount object
        return BankAccount(
            id=str(uuid.uuid4()),
            account_number=account_number,
            iban=iban,
            account_type=account_type,
            bank=bank,
            balance=balance,
            currency=currency,
            created_date=created_date,
            last_transaction_date=last_transaction_date,
        )

    def generate_bank_accounts(self, count: int = 1) -> list[BankAccount]:
        """Generate multiple random bank accounts.

        Args:
            count: The number of bank accounts to generate

        Returns:
            A list of BankAccount objects with randomly generated data.
        """
        return [self.generate_bank_account() for _ in range(count)]
