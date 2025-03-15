from pathlib import Path
import random
from typing import Any
from datamimic_ce.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.utils.file_content_storage import FileContentStorage
from datamimic_ce.utils.file_util import FileUtil


class InsuranceCoverageGenerator(BaseDomainGenerator):
    """Generator for insurance coverage data."""

    def __init__(self, dataset: str = "US"):
        """Initialize the insurance coverage generator.

        Args:
            dataset: The country code to use for data generation
        """
        self._dataset = dataset

    def get_random_coverage(self) -> dict[str, Any]:
        file_path = Path(__file__).parent / "data" / f"insurance_coverages_{self._dataset}.csv"
        loaded_data = FileContentStorage.load_file_with_custom_function(str(file_path), lambda: FileUtil.read_csv_having_weight_column(file_path))
        coverage_data= random.choices(loaded_data, weights=[item["weight"] for item in loaded_data], k=1)[0]
        
        return {
            "name": coverage_data["name"],
            "code": coverage_data["code"],
            "product_code": coverage_data["product_code"],
            "description": coverage_data["description"],
            "min_coverage": coverage_data["min_coverage"],
            "max_coverage": coverage_data["max_coverage"],
        }
