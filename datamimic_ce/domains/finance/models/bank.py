from typing import Any

from datamimic_ce.domains.common.literal_generators.phone_number_generator import PhoneNumberGenerator
from datamimic_ce.domains.common.literal_generators.string_generator import StringGenerator
from datamimic_ce.domains.domain_core import BaseEntity
from datamimic_ce.domains.domain_core.property_cache import property_cache
from datamimic_ce.domains.finance.generators.bank_generator import BankGenerator


class Bank(BaseEntity):
    """Bank information associated with a bank account."""

    def __init__(self, bank_generator: BankGenerator):
        super().__init__()
        self._bank_generator = bank_generator

    @property
    @property_cache
    def bank_data(self) -> dict:
        return self._bank_generator.generate_bank_data()

    @property
    @property_cache
    def name(self) -> str:
        return self.bank_data["name"]

    @property
    @property_cache
    def swift_code(self) -> str:
        return self.bank_data["swift_code"]

    @property
    @property_cache
    def routing_number(self) -> str:
        return self.bank_data["routing_number"]

    @property
    @property_cache
    def bank_code(self) -> str:
        return self.swift_code

    @property
    @property_cache
    def bic(self) -> str:
        #  embed dataset country code (US/DE) into BIC pattern for consistency
        ds = getattr(self._bank_generator, "dataset", "US").upper()
        # Basic 8-char BIC: 4 letters bank + 2-letter country + 2 alnum location
        pattern = f"[A-Z]{{4}}{ds}[A-Z0-9]{{2}}"
        return StringGenerator.rnd_str_from_regex(pattern)

    @property
    @property_cache
    def bin(self) -> str:
        return StringGenerator.rnd_str_from_regex("[0-9]{4}")

    @property
    @property_cache
    def customer_service_phone(self) -> str:
        """Get a customer service phone number for the bank.

        Returns:
            A formatted phone number string.
        """
        #  use shared PhoneNumberGenerator with dataset for consistent formatting
        ds = getattr(self._bank_generator, "dataset", "US")
        return PhoneNumberGenerator(dataset=ds).generate()

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "swift_code": self.swift_code,
            "routing_number": self.routing_number,
            "bank_code": self.bank_code,
            "bic": self.bic,
            "bin": self.bin,
            "customer_service_phone": self.customer_service_phone,
        }
