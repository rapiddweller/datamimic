import random
from pathlib import Path

from datamimic_ce.domains.domain_core.base_domain_generator import DatasetAwareDomainGenerator
from datamimic_ce.domains.domain_core.datasets.path import dataset_path
from datamimic_ce.domains.domain_core.runtime.rng_uuid import uuid4_from_random
from datamimic_ce.domains.shared.datasets.loader import read_weighted_records


class InsuranceCompanyGenerator(DatasetAwareDomainGenerator):
    """Generator for insurance company data."""

    def __init__(
        self,
        dataset: str | None = None,
        rng: random.Random | None = None,
    ):
        """Initialize the insurance company generator.

        Args:
            dataset: The country code to use for data generation
            rng: Optional seeded random instance for deterministic output.
        """
        super().__init__(dataset=dataset, rng=rng)

    def generate_id_candidate(self) -> str:
        return uuid4_from_random(self.rng)

    def get_random_company(self) -> dict[str, str]:
        #  use unified dataset path helper
        file_path = dataset_path("insurance", f"companies_{self._dataset}.csv", start=Path(__file__))
        loaded_wgt, loaded_data = read_weighted_records(file_path, "weight")
        company_data = self._rng.choices(loaded_data, weights=loaded_wgt, k=1)[0]

        return {
            "name": company_data["name"],
            "code": company_data["code"],
            "founded_year": company_data["founded_year"],
            "headquarters": company_data["headquarters"],
            "website": company_data["website"],
        }
