from pathlib import Path
import random
from datamimic_ce.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.domains.common.generators.address_generator import AddressGenerator
from datamimic_ce.domains.common.generators.person_generator import PersonGenerator
from datamimic_ce.domains.common.literal_generators.phone_number_generator import PhoneNumberGenerator
from datamimic_ce.utils.file_content_storage import FileContentStorage
from datamimic_ce.utils.file_util import FileUtil

class PoliceOfficerGenerator(BaseDomainGenerator):
    """Generate police officer data."""

    def __init__(self, dataset: str = "US"):
        """Initialize the police officer generator.

        Args:
            dataset: The dataset to use for data generation
        """
        self._dataset = dataset
        self._person_generator = PersonGenerator(dataset=dataset)
        self._address_generator = AddressGenerator(dataset=dataset)
        self._phone_number_generator = PhoneNumberGenerator(dataset=dataset)

    @property
    def person_generator(self) -> PersonGenerator:
        return self._person_generator
    
    @property
    def address_generator(self) -> AddressGenerator:
        return self._address_generator
    
    @property
    def phone_number_generator(self) -> PhoneNumberGenerator:
        return self._phone_number_generator

    def get_rank(self) -> str:
        """Get a random rank.

        Returns:
            A random rank.
        """
        file_path = Path(__file__).parent / "data" / f"police_ranks_{self._dataset}.csv"
        loaded_data = FileContentStorage.load_file_with_custom_func(str(file_path), lambda: FileUtil.read_csv(str(file_path)))
        weights = [row["weight"] for row in loaded_data]
        return random.choices(loaded_data, weights=weights, k=1)[0]["rank"]

    def get_department(self) -> str:
        """Get a random department.

        Returns:
            A random department.
        """
        file_path = Path(__file__).parent / "data" / f"police_departments_{self._dataset}.csv"
        loaded_data = FileContentStorage.load_file_with_custom_func(str(file_path), lambda: FileUtil.read_csv(str(file_path)))
        weights = [row["weight"] for row in loaded_data]
        return random.choices(loaded_data, weights=weights, k=1)[0]["department"]
