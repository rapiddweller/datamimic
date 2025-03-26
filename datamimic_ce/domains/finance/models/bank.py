from typing import Any

from datamimic_ce.domain_core.base_entity import BaseEntity
from datamimic_ce.domain_core.property_cache import property_cache
from datamimic_ce.domains.finance.generators.bank_generator import BankGenerator
from datamimic_ce.utils.data_generation_ce_util import DataGenerationCEUtil


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
        return DataGenerationCEUtil.rnd_str_from_regex("[A-Z]{4}DE[A-Z0-9]{2}")

    @property
    @property_cache
    def bin(self) -> str:
        return DataGenerationCEUtil.rnd_str_from_regex("[0-9]{4}")

    @property
    @property_cache
    def customer_service_phone(self) -> str:
        """Get a customer service phone number for the bank.

        Returns:
            A formatted phone number string.
        """
        if hasattr(self._bank_generator, "dataset") and self._bank_generator.dataset == "de_DE":
            # German format
            return "+49 " + DataGenerationCEUtil.rnd_str_from_regex("[0-9]{3} [0-9]{5,7}")
        else:
            # US format
            return "+1 " + DataGenerationCEUtil.rnd_str_from_regex("[0-9]{3}-[0-9]{3}-[0-9]{4}")

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
