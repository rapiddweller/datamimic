# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Credit Card Service.

This module provides service functions for generating and managing credit cards.
"""

import random
import uuid
from datetime import date, datetime, timedelta

from datamimic_ce.domains.finance.data_loaders.credit_card_loader import CreditCardLoader
from datamimic_ce.domains.finance.models.credit_card import CreditCard, CreditCardType
from datamimic_ce.domains.finance.utils.validation_utils import generate_luhn_number


class CreditCardService:
    """Service for generating and managing credit cards."""

    def __init__(self, dataset: str = "US"):
        """Initialize the credit card service.

        Args:
            dataset: The country code (e.g., "US", "DE") to use for data generation.
        """
        self.dataset = dataset
        # Cache the loaded card types
        self._card_types_by_weight = CreditCardLoader._load_card_types_by_weight(dataset)

    def generate_card_type(self) -> CreditCardType:
        """Generate a random credit card type based on weighted probabilities.

        Returns:
            A CreditCardType object with randomly generated data.
        """
        if not self._card_types_by_weight:
            raise ValueError(f"No card types found for dataset {self.dataset}")

        # Select a card type based on weights
        card_types = [ct[0] for ct in self._card_types_by_weight]
        weights = [ct[1] for ct in self._card_types_by_weight]

        selected_card_type = random.choices(card_types, weights=weights, k=1)[0]

        # Create and return a CreditCardType object
        return CreditCardType(
            type=selected_card_type.get("type", "UNKNOWN"),
            prefixes=selected_card_type.get("prefix", ["4"]),  # Default to VISA prefix
            length=selected_card_type.get("length", 16),
            cvv_length=selected_card_type.get("cvv_length", 3),
        )

    def generate_card_number(self, card_type: CreditCardType) -> str:
        """Generate a valid credit card number for the given card type.

        Args:
            card_type: The credit card type to generate a number for

        Returns:
            A valid credit card number.
        """
        # Select a random prefix from the available prefixes
        prefix = random.choice(card_type.prefixes)

        # Generate a valid number using the Luhn algorithm
        return generate_luhn_number(prefix, card_type.length)

    def generate_cvv(self, card_type: CreditCardType) -> str:
        """Generate a random CVV for the given card type.

        Args:
            card_type: The credit card type to generate a CVV for

        Returns:
            A randomly generated CVV.
        """
        # Generate a random CVV of the specified length
        return "".join([str(random.randint(0, 9)) for _ in range(card_type.cvv_length)])

    def generate_expiration_date(self) -> tuple[int, int]:
        """Generate a random expiration date in the future.

        Returns:
            A tuple containing (month, year) for the expiration date.
        """
        # Current date
        now = datetime.now()

        # Generate an expiration date between 1 and 5 years in the future
        years_in_future = random.randint(1, 5)
        expiration_date = now + timedelta(days=365 * years_in_future)

        return expiration_date.month, expiration_date.year

    def generate_card_holder(self) -> str:
        """Generate a random card holder name.

        Returns:
            A randomly generated card holder name.
        """
        # List of common first names
        first_names = [
            "John",
            "Jane",
            "Michael",
            "Emily",
            "David",
            "Sarah",
            "Robert",
            "Jennifer",
            "William",
            "Elizabeth",
            "Richard",
            "Linda",
            "Joseph",
            "Patricia",
            "Thomas",
            "Barbara",
        ]

        # List of common last names
        last_names = [
            "Smith",
            "Johnson",
            "Williams",
            "Jones",
            "Brown",
            "Davis",
            "Miller",
            "Wilson",
            "Moore",
            "Taylor",
            "Anderson",
            "Thomas",
            "Jackson",
            "White",
            "Harris",
            "Martin",
        ]

        # Generate a random first and last name
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)

        return f"{first_name} {last_name}"

    def generate_credit_card(
        self,
        card_type: CreditCardType | None = None,
        card_number: str | None = None,
        card_holder: str | None = None,
        expiration_month: int | None = None,
        expiration_year: int | None = None,
        cvv: str | None = None,
        credit_limit: float | None = None,
        current_balance: float | None = None,
        bank_name: str | None = None,
    ) -> CreditCard:
        """Generate a random credit card.

        Args:
            card_type: Optional predefined card type to use
            card_number: Optional predefined card number to use
            card_holder: Optional predefined card holder name to use
            expiration_month: Optional predefined expiration month to use
            expiration_year: Optional predefined expiration year to use
            cvv: Optional predefined CVV to use
            credit_limit: Optional predefined credit limit to use
            current_balance: Optional predefined current balance to use
            bank_name: Optional predefined bank name to use

        Returns:
            A CreditCard object with randomly generated data.
        """
        # Generate values for any parameters not provided
        if card_type is None:
            card_type = self.generate_card_type()

        if card_number is None:
            card_number = self.generate_card_number(card_type)

        if card_holder is None:
            card_holder = self.generate_card_holder()

        if expiration_month is None or expiration_year is None:
            month, year = self.generate_expiration_date()
            expiration_month = month if expiration_month is None else expiration_month
            expiration_year = year if expiration_year is None else expiration_year

        if cvv is None:
            cvv = self.generate_cvv(card_type)

        if credit_limit is None:
            # Generate a random credit limit between 1000 and 20000
            credit_limit = round(random.uniform(1000, 20000), 2)

        if current_balance is None:
            # Generate a random balance between 0 and the credit limit
            current_balance = round(random.uniform(0, credit_limit * 0.8), 2)

        if bank_name is None:
            # List of common bank names
            bank_names = [
                "First National Bank",
                "City Bank",
                "Capital One",
                "Wells Fargo",
                "Bank of America",
                "Chase",
                "Deutsche Bank",
                "Commerzbank",
            ]
            bank_name = random.choice(bank_names)

        # Generate an issue date between 1 and 5 years ago
        days_ago = random.randint(365, 365 * 5)
        issue_date = date.today() - timedelta(days=days_ago)

        # Create and return a CreditCard object
        return CreditCard(
            id=str(uuid.uuid4()),
            card_number=card_number,
            card_holder=card_holder,
            card_type=card_type,
            expiration_month=expiration_month,
            expiration_year=expiration_year,
            cvv=cvv,
            is_active=True,
            credit_limit=credit_limit,
            current_balance=current_balance,
            issue_date=issue_date,
            bank_name=bank_name,
        )

    def generate_credit_cards(self, count: int = 1) -> list[CreditCard]:
        """Generate multiple random credit cards.

        Args:
            count: The number of credit cards to generate

        Returns:
            A list of CreditCard objects with randomly generated data.
        """
        return [self.generate_credit_card() for _ in range(count)]
