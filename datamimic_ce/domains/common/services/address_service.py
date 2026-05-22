from random import Random

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

    DATASET_PATTERNS = (
        "common/city/city_{CC}.csv",
        "common/country_{CC}.csv",
        "common/street/street_{CC}.csv",
    )

    def __init__(
        self,
        dataset: str | None = None,
        rng: Random | None = None,
    ):
        super().__init__(AddressGenerator(dataset=dataset, rng=rng), Address)

    @classmethod
    def attribute_specs(cls) -> tuple[FieldSpec, ...]:
        return ADDRESS_SCHEMA.fields
