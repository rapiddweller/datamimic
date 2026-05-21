import random

from datamimic_ce.domains.common.generators.address_generator import AddressGenerator
from datamimic_ce.domains.common.models.address import Address
from datamimic_ce.domains.domain_core import BaseDomainService
from datamimic_ce.domains.domain_core.attribute_catalog import AttributeSpec, specs


class AddressService(BaseDomainService[Address]):
    """Service for managing address data.

    This class provides methods for creating, retrieving, and managing address data.
    """

    def __init__(
        self,
        dataset: str | None = None,
        rng: random.Random | None = None,
    ):
        super().__init__(AddressGenerator(dataset=dataset, rng=rng), Address)

    @classmethod
    def attribute_specs(cls) -> tuple[AttributeSpec, ...]:
        return specs(
            ("street", "str", "Street or thoroughfare name."),
            ("house_number", "str", "House or building number."),
            ("city", "str", "City or locality name."),
            ("state", "str", "State, province, or region."),
            ("postal_code", "str", "Postal or ZIP code."),
            ("country", "str", "Human-readable country name."),
            ("country_code", "str", "ISO 3166-1 alpha-2 country code."),
            ("phone", "str", "Landline phone number."),
            ("mobile_phone", "str", "Mobile phone number."),
            ("fax", "str", "Fax number."),
            ("organization", "str", "Associated organization name."),
            ("full_address", "str", "Formatted full address string."),
        )

    @staticmethod
    def supported_datasets() -> set[str]:
        from pathlib import Path

        from datamimic_ce.domains.utils.supported_datasets import compute_supported_datasets

        patterns = [
            "common/city/city_{CC}.csv",
            "common/country_{CC}.csv",
            "common/street/street_{CC}.csv",
        ]
        return compute_supported_datasets(patterns, start=Path(__file__))
