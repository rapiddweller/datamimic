# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Finance data generators.

This module provides generator classes for finance-related data.
"""

import uuid
from typing import Any

from datamimic_ce.core.interfaces import Generator
from datamimic_ce.domains.finance.services.bank_account_service import BankAccountService
from datamimic_ce.domains.finance.services.credit_card_service import CreditCardService


class BankAccountGenerator(Generator):
    """Generator for bank account data."""

    def __init__(self, dataset: str = "US", **kwargs):
        """Initialize the bank account generator.

        Args:
            dataset: The country code to use for data generation
            **kwargs: Additional arguments to pass to the generator
        """
        super().__init__(**kwargs)
        self.service = BankAccountService(dataset=dataset)

    def generate(self) -> dict[str, Any]:
        """Generate a bank account.

        Returns:
            A dictionary containing bank account data
        """
        account = self.service.generate_bank_account()
        return account.dict()


class CreditCardGenerator(Generator):
    """Generator for credit card data."""

    def __init__(self, dataset: str = "US", **kwargs):
        """Initialize the credit card generator.

        Args:
            dataset: The country code to use for data generation
            **kwargs: Additional arguments to pass to the generator
        """
        super().__init__(**kwargs)
        self.service = CreditCardService(dataset=dataset)

    def generate(self) -> dict[str, Any]:
        """Generate a credit card.

        Returns:
            A dictionary containing credit card data
        """
        card = self.service.generate_credit_card()
        # Convert the card to a dictionary
        card_dict = card.dict()
        # Add additional derived properties
        card_dict["masked_card_number"] = card.masked_card_number
        card_dict["expiration_date_str"] = card.expiration_date_str
        card_dict["is_expired"] = card.is_expired
        return card_dict


class FinanceDataGenerator(Generator):
    """Generator for comprehensive finance data including bank accounts and credit cards."""

    def __init__(
        self,
        dataset: str = "US",
        include_bank_accounts: bool = True,
        include_credit_cards: bool = True,
        num_bank_accounts: int = 1,
        num_credit_cards: int = 1,
        **kwargs,
    ):
        """Initialize the finance data generator.

        Args:
            dataset: The country code to use for data generation
            include_bank_accounts: Whether to include bank accounts in the generated data
            include_credit_cards: Whether to include credit cards in the generated data
            num_bank_accounts: The number of bank accounts to generate
            num_credit_cards: The number of credit cards to generate
            **kwargs: Additional arguments to pass to the generator
        """
        super().__init__(**kwargs)
        self.dataset = dataset
        self.include_bank_accounts = include_bank_accounts
        self.include_credit_cards = include_credit_cards
        self.num_bank_accounts = num_bank_accounts
        self.num_credit_cards = num_credit_cards
        self.bank_account_service = BankAccountService(dataset=dataset)
        self.credit_card_service = CreditCardService(dataset=dataset)

    def generate(self) -> dict[str, Any]:
        """Generate comprehensive finance data.

        Returns:
            A dictionary containing finance data including bank accounts and credit cards
        """
        result = {
            "id": str(uuid.uuid4()),
            "dataset": self.dataset,
        }

        if self.include_bank_accounts:
            accounts = self.bank_account_service.generate_bank_accounts(count=self.num_bank_accounts)
            result["bank_accounts"] = [account.dict() for account in accounts]

        if self.include_credit_cards:
            cards = self.credit_card_service.generate_credit_cards(count=self.num_credit_cards)
            # Convert cards to dictionaries and add derived properties
            card_dicts = []
            for card in cards:
                card_dict = card.dict()
                card_dict["masked_card_number"] = card.masked_card_number
                card_dict["expiration_date_str"] = card.expiration_date_str
                card_dict["is_expired"] = card.is_expired
                card_dicts.append(card_dict)
            result["credit_cards"] = card_dicts

        return result
