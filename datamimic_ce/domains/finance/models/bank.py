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
    def bank_data(self) -> dict[str, str]:
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
        return self._bank_generator.generate_bic()

    @property
    @property_cache
    def bin(self) -> str:
        return self._bank_generator.generate_bin()

    @property
    @property_cache
    def customer_service_phone(self) -> str:
        return self._bank_generator.generate_customer_service_phone()

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "swift_code": self.swift_code,
            "routing_number": self.routing_number,
            "bank_code": self.bank_code,
            "bic": self.bic,
            "bin": self.bin,
            "customer_service_phone": self.customer_service_phone,
        }
