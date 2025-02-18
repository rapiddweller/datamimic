# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random

from mimesis import Finance, Payment, Person

from datamimic_ce.generators.generator import Generator


class CreditCardGenerator(Generator):
    """Generate credit card numbers ensuring only digits."""

    def __init__(self, card_type: str | None = None):
        """
        Initialize CreditCardGenerator.

        Args:
            card_type (str): Optional card type (not implemented yet)
        """
        self._payment = Payment()
        self._card_type = card_type

    def generate(self) -> str:
        """Generate a credit card number.

        Returns:
            str: Generated credit card number (digits only)
        """
        # Payment.credit_card_number() might return spaces or dashes
        number = self._payment.credit_card_number()
        # Remove any non-digit characters
        return "".join(ch for ch in number if ch.isdigit())


class CurrencyGenerator(Generator):
    """Generate currency related data, either symbol+amount or code only."""

    def __init__(self, code_only: bool = False):
        """
        Initialize CurrencyGenerator.

        Args:
            code_only (bool): Whether to return only the currency code
        """
        self._finance = Finance()
        self._code_only = code_only

    def generate(self) -> str:
        """Generate currency data.

        Returns:
            str: Currency code or symbol+amount
        """
        if self._code_only:
            return self._finance.currency_iso_code()
        return f"{self._finance.currency_symbol()}{self._finance.price()}"


class JobTitleGenerator(Generator):
    """Generate realistic job titles with optional level and locale."""

    def __init__(self, locale: str = "en", level: str | None = None):
        """
        Initialize JobTitleGenerator.

        Args:
            locale (str): Locale for job titles
            level (str): Optional job level ('junior', 'senior', 'manager', 'executive')
        """
        self._person = Person(locale)
        self._level = level.lower() if level else None
        self._departments = [
            "Operations",
            "Technology",
            "Sales",
            "Marketing",
            "Finance",
            "Human Resources",
            "Research",
            "Development",
            "Product",
            "Engineering",
        ]

    def generate(self) -> str:
        """Generate a job title.

        Returns:
            str: Generated job title with optional level prefix/suffix
        """
        title = self._person.occupation()
        if self._level:
            if self._level == "junior":
                return f"Junior {title}"
            elif self._level == "senior":
                return f"Senior {title}"
            elif self._level == "manager":
                return f"{title} Manager"
            elif self._level == "executive":
                department = random.choice(self._departments)
                return f"Chief {department} Officer"
        return title
