import random
from pathlib import Path
from typing import Any

from datamimic_ce.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.domains.insurance.generators.insurance_coverage_generator import InsuranceCoverageGenerator
from datamimic_ce.utils.file_util import FileUtil


class InsuranceProductGenerator(BaseDomainGenerator):
    """Generator for insurance product data."""

    def __init__(self, dataset: str | None = None):
        """Initialize the insurance product generator.

        Args:
            dataset: The country code to use for data generation
        """
        self._dataset = dataset or "US"
        self._insurance_coverage_generator = InsuranceCoverageGenerator(dataset=dataset)

    @property
    def insurance_coverage_generator(self) -> InsuranceCoverageGenerator:
        return self._insurance_coverage_generator

    def get_random_product(self) -> dict[str, Any]:
        file_path = (
            Path(__file__).parent.parent.parent.parent / "domain_data" / "insurance" / f"products_{self._dataset}.csv"
        )
        loaded_wgt, loaded_data = FileUtil.read_csv_having_weight_column(file_path, "weight")
        product_data = random.choices(loaded_data, weights=loaded_wgt, k=1)[0]

        return {
            "type": product_data["type"],
            "code": product_data["code"],
            "description": product_data["description"],
        }
