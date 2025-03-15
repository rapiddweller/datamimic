from pathlib import Path
import random
from typing import Any
from datamimic_ce.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.domains.insurance.generators.insurance_coverage import InsuranceCoverageGenerator
from datamimic_ce.utils.file_content_storage import FileContentStorage
from datamimic_ce.utils.file_util import FileUtil


class InsuranceProductGenerator(BaseDomainGenerator):
    """Generator for insurance product data."""

    def __init__(self, dataset: str = "US"):
        """Initialize the insurance product generator.

        Args:
            dataset: The country code to use for data generation
        """
        self._dataset = dataset
        self._insurance_coverage_generator = InsuranceCoverageGenerator(dataset=dataset)

    def get_random_product(self) -> dict[str, Any]:
        file_path = Path(__file__).parent / "data" / f"insurance_products_{self._dataset}.csv"
        loaded_data = FileContentStorage.load_file_with_custom_function(str(file_path), lambda: FileUtil.read_csv_having_weight_column(file_path))
        product_data= random.choices(loaded_data, weights=[item["weight"] for item in loaded_data], k=1)[0]
        
        return {
            "type": product_data["type"],
            "code": product_data["code"],
            "description": product_data["description"],
        }
