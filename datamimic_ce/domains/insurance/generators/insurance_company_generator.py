import random
from pathlib import Path
from typing import Any

from datamimic_ce.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.utils.file_util import FileUtil


class InsuranceCompanyGenerator(BaseDomainGenerator):
    """Generator for insurance company data."""

    def __init__(self, dataset: str | None = None):
        """Initialize the insurance company generator.

        Args:
            dataset: The country code to use for data generation
        """
        self._dataset = dataset or "US"

    def get_random_company(self) -> dict[str, Any]:
        file_path = (
            Path(__file__).parent.parent.parent.parent / "domain_data" / "insurance" / f"companies_{self._dataset}.csv"
        )
        loaded_wgt, loaded_data = FileUtil.read_csv_having_weight_column(file_path, "weight")
        company_data = random.choices(loaded_data, weights=loaded_wgt, k=1)[0]

        return {
            "name": company_data["name"],
            "code": company_data["code"],
            "founded_year": company_data["founded_year"],
            "headquarters": company_data["headquarters"],
            "website": company_data["website"],
        }
