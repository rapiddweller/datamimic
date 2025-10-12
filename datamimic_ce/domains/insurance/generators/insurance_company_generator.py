import random
from pathlib import Path
from typing import Any

from datamimic_ce.domains.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.domains.utils.dataset_path import dataset_path
from datamimic_ce.utils.file_util import FileUtil


class InsuranceCompanyGenerator(BaseDomainGenerator):
    """Generator for insurance company data."""

    def __init__(self, dataset: str | None = None, rng: random.Random | None = None):
        """Initialize the insurance company generator.

        Args:
            dataset: The country code to use for data generation
        """
        self._dataset = (dataset or "US").upper()
        self._rng: random.Random = rng or random.Random()
        self._last_company_code: str | None = None
        self._last_founded_year: str | None = None

    @property
    def rng(self) -> random.Random:
        return self._rng

    def get_random_company(self) -> dict[str, Any]:
        #  use unified dataset path helper
        file_path = dataset_path("insurance", f"companies_{self._dataset}.csv", start=Path(__file__))
        loaded_wgt, loaded_data = FileUtil.read_csv_having_weight_column(file_path, "weight")
        # Avoid immediate repetition by code and founded_year when feasible
        pool = loaded_data
        pool_w = loaded_wgt
        if len(loaded_data) > 1:
            filtered = [
                row
                for row in loaded_data
                if row.get("code") != self._last_company_code and row.get("founded_year") != self._last_founded_year
            ]
            if filtered:
                pool = filtered
                pool_w = [float(row.get("weight", 1.0) or 1.0) for row in filtered]
        company_data = self._rng.choices(pool, weights=pool_w, k=1)[0]
        self._last_company_code = company_data.get("code")
        self._last_founded_year = company_data.get("founded_year")

        return {
            "name": company_data["name"],
            "code": company_data["code"],
            "founded_year": company_data["founded_year"],
            "headquarters": company_data["headquarters"],
            "website": company_data["website"],
        }
