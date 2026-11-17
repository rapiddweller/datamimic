import random
from pathlib import Path
from typing import TypedDict

from datamimic_ce.domains.domain_core.base_domain_generator import DatasetAwareDomainGenerator
from datamimic_ce.domains.domain_core.datasets.path import dataset_path
from datamimic_ce.domains.shared.datasets.loader import read_weighted_records


class InsuranceCoverageData(TypedDict):
    name: str
    code: str
    product_code: str
    description: str
    min_coverage: str
    max_coverage: str


class InsuranceCoverageGenerator(DatasetAwareDomainGenerator):
    """Generator for insurance coverage data."""

    def __init__(
        self,
        dataset: str | None = None,
        rng: random.Random | None = None,
    ):
        """Initialize the insurance coverage generator.

        Args:
            dataset: The country code to use for data generation
            rng: Optional seeded random instance for deterministic output.
        """
        super().__init__(dataset=dataset, rng=rng)

    def get_random_coverage(self) -> InsuranceCoverageData:
        #  centralize dataset path building for maintainability
        file_path = dataset_path("insurance", f"coverages_{self._dataset}.csv", start=Path(__file__))
        weights, rows = read_weighted_records(file_path, "weight")
        coverage_data = self._rng.choices(rows, weights=weights, k=1)[0]

        return {
            "name": coverage_data["name"],
            "code": coverage_data["code"],
            "product_code": coverage_data["product_code"],
            "description": coverage_data["description"],
            "min_coverage": coverage_data["min_coverage"],
            "max_coverage": coverage_data["max_coverage"],
        }
