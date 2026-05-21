import random

from datamimic_ce.domains.common.generators.address_generator import AddressGenerator
from datamimic_ce.domains.common.models.address import Address
from datamimic_ce.domains.domain_core import BaseDomainService
from datamimic_ce.domains.domain_core.attribute_catalog import ADDRESS_FIELDS, EntitySchema, FieldSpec, field

ADDRESS_SCHEMA = EntitySchema(
    "Address",
    (
        *ADDRESS_FIELDS,
        field("phone", str, "Landline phone number."),
        field("mobile_phone", str, "Mobile phone number."),
        field("fax", str, "Fax number."),
        field("organization", str, "Associated organization name."),
        field("full_address", str, "Formatted full address string."),
    ),
)


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
    def attribute_specs(cls) -> tuple[FieldSpec, ...]:
        return ADDRESS_SCHEMA.fields

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
