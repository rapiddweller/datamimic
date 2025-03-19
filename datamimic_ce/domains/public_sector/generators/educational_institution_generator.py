from datamimic_ce.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.domains.common.generators.address_generator import AddressGenerator
from datamimic_ce.domains.common.literal_generators.email_address_generator import EmailAddressGenerator
from datamimic_ce.domains.common.literal_generators.phone_number_generator import PhoneNumberGenerator


class EducationalInstitutionGenerator(BaseDomainGenerator):
    """Generator for educational institution data."""

    def __init__(self, dataset: str | None = None):
        """Initialize the educational institution generator.

        Args:
            dataset: The country code to use for data generation
        """
        self._dataset = dataset or "US"
        self._address_generator = AddressGenerator(dataset=dataset)
        self._phone_number_generator = PhoneNumberGenerator(dataset=dataset)
        self._email_generator = EmailAddressGenerator(dataset=dataset)

    @property
    def address_generator(self) -> AddressGenerator:
        return self._address_generator

    @property
    def phone_number_generator(self) -> PhoneNumberGenerator:
        return self._phone_number_generator

    @property
    def email_generator(self) -> EmailAddressGenerator:
        return self._email_generator
