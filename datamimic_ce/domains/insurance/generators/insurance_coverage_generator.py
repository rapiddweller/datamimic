import random
from pathlib import Path
from typing import Any

from datamimic_ce.domains.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.domains.utils.dataset_path import dataset_path
from datamimic_ce.utils.file_util import FileUtil


class InsuranceCoverageGenerator(BaseDomainGenerator):
    """Generator for insurance coverage data."""

    def __init__(self, dataset: str | None = None, rng: random.Random | None = None):
        """Initialize the insurance coverage generator.

        Args:
            dataset: The country code to use for data generation
        """
        self._dataset = dataset or "US"
        self._rng: random.Random = rng or random.Random()
        self._last_coverage_code: str | None = None
        self._last_product_code: str | None = None
        self._last_min_coverage: str | None = None
        self._last_max_coverage: str | None = None

    def get_random_coverage(self) -> dict[str, Any]:
        #  centralize dataset path building for maintainability
        file_path = dataset_path("insurance", f"coverages_{self._dataset}.csv", start=Path(__file__))
        weights, rows = FileUtil.read_csv_having_weight_column(file_path, "weight")
        # Avoid immediate repetition by code and by product_code if possible
        pool = rows
        pool_w = weights
        if len(rows) > 1:
            filtered = [
                row
                for row in rows
                if row.get("code") != self._last_coverage_code and row.get("product_code") != self._last_product_code
            ]
            if filtered:
                pool = filtered
                pool_w = [float(row.get("weight", 1.0) or 1.0) for row in filtered]
        coverage_data = self._rng.choices(pool, weights=pool_w, k=1)[0]
        self._last_coverage_code = coverage_data.get("code")
        self._last_product_code = coverage_data.get("product_code")

        # Avoid repeating min_coverage if possible by reselecting once
        if self._last_min_coverage is not None and coverage_data.get("min_coverage") == self._last_min_coverage:
            alt = [r for r in rows if r.get("min_coverage") != self._last_min_coverage]
            if alt:
                alt_w = [float(r.get("weight", 1.0) or 1.0) for r in alt]
                coverage_data = self._rng.choices(alt, weights=alt_w, k=1)[0]
        self._last_min_coverage = coverage_data.get("min_coverage")
        if self._last_max_coverage is not None and coverage_data.get("max_coverage") == self._last_max_coverage:
            alt2 = [r for r in rows if r.get("max_coverage") != self._last_max_coverage]
            if alt2:
                alt2_w = [float(r.get("weight", 1.0) or 1.0) for r in alt2]
                coverage_data = self._rng.choices(alt2, weights=alt2_w, k=1)[0]
        self._last_max_coverage = coverage_data.get("max_coverage")

        return {
            "name": coverage_data["name"],
            "code": coverage_data["code"],
            "product_code": coverage_data["product_code"],
            "description": coverage_data["description"],
            "min_coverage": coverage_data["min_coverage"],
            "max_coverage": coverage_data["max_coverage"],
        }
