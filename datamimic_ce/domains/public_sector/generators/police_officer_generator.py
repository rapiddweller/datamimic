import random
from pathlib import Path

from datamimic_ce.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.domains.common.generators.address_generator import AddressGenerator
from datamimic_ce.domains.common.generators.person_generator import PersonGenerator
from datamimic_ce.domains.common.literal_generators.email_address_generator import EmailAddressGenerator
from datamimic_ce.domains.common.literal_generators.phone_number_generator import PhoneNumberGenerator
from datamimic_ce.utils.file_util import FileUtil


class PoliceOfficerGenerator(BaseDomainGenerator):
    """Generate police officer data."""

    def __init__(self, dataset: str | None = None):
        """Initialize the police officer generator.

        Args:
            dataset: The dataset to use for data generation
        """
        self._dataset = dataset or "US"
        self._person_generator = PersonGenerator(dataset=dataset, min_age=21)
        self._address_generator = AddressGenerator(dataset=dataset)
        self._phone_number_generator = PhoneNumberGenerator(dataset=dataset)
        self._email_address_generator = EmailAddressGenerator(dataset=dataset)

    @property
    def person_generator(self) -> PersonGenerator:
        return self._person_generator

    @property
    def address_generator(self) -> AddressGenerator:
        return self._address_generator

    @property
    def phone_number_generator(self) -> PhoneNumberGenerator:
        return self._phone_number_generator

    @property
    def email_address_generator(self) -> EmailAddressGenerator:
        return self._email_address_generator

    def get_rank(self) -> str:
        """Get a random rank.

        Returns:
            A random rank.
        """
        file_path = (
            Path(__file__).parents[3] / "domain_data" / "public_sector" / "police" / f"ranks_{self._dataset}.csv"
        )
        loaded_weights, loaded_data = FileUtil.read_csv_having_weight_column(file_path, "weight")
        return random.choices(loaded_data, weights=loaded_weights, k=1)[0].get("rank")

    def get_department(self) -> str:
        """Get a random department.

        Returns:
            A random department.
        """
        file_path = (
            Path(__file__).parents[3] / "domain_data" / "public_sector" / "police" / f"departments_{self._dataset}.csv"
        )
        loaded_weights, loaded_data = FileUtil.read_csv_having_weight_column(file_path, "weight")
        return random.choices(loaded_data, weights=loaded_weights, k=1)[0].get("department_id")
