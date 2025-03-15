from pathlib import Path
import random
from typing import Any
from datamimic_ce.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.utils.file_content_storage import FileContentStorage
from datamimic_ce.utils.file_util import FileUtil


class InsuranceCompanyGenerator(BaseDomainGenerator):
    """Generator for insurance company data."""

    def __init__(self, dataset: str = "US"):
        """Initialize the insurance company generator.

        Args:
            dataset: The country code to use for data generation
        """
        self._dataset = dataset

    def get_random_company(self) -> dict[str, Any]:
        file_path = Path(__file__).parent / "data" / f"insurance_companies_{self._dataset}.csv"
        loaded_data = FileContentStorage.load_file_with_custom_function(str(file_path), lambda: FileUtil.read_csv_having_weight_column(file_path))
        company_data= random.choices(loaded_data, weights=[item["weight"] for item in loaded_data], k=1)[0]
        
        return {
            "name": company_data["name"],
            "code": company_data["code"],
            "founded_year": company_data["founded_year"],
            "headquarters": company_data["headquarters"],
            "website": company_data["website"],
        }
