import random
from pathlib import Path
from typing import Any

from datamimic_ce.domains.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.domains.insurance.generators.insurance_coverage_generator import InsuranceCoverageGenerator
from datamimic_ce.domains.utils.dataset_loader import load_weighted_values_try_dataset, pick_one_weighted


class InsuranceProductGenerator(BaseDomainGenerator):
    """Generator for insurance product data."""

    def __init__(self, dataset: str | None = None, rng: random.Random | None = None):
        """Initialize the insurance product generator.

        Args:
            dataset: The country code to use for data generation
        """
        self._dataset = dataset or "US"
        self._rng: random.Random = rng or random.Random()
        self._insurance_coverage_generator = InsuranceCoverageGenerator(dataset=dataset, rng=self._rng)
        self._last_product_type: str | None = None

    @property
    def insurance_coverage_generator(self) -> InsuranceCoverageGenerator:
        return self._insurance_coverage_generator

    @property
    def dataset(self) -> str:
        return self._dataset

    @property
    def rng(self) -> random.Random:
        return self._rng

    def get_random_product(self) -> dict[str, Any]:
        #  centralized weighted loading via loaders with base filename only
        values, weights = load_weighted_values_try_dataset(
            "insurance", "products.csv", dataset=self._dataset, start=Path(__file__)
        )
        # values are expected to be serialized dict-like fields or codes; we prefer SPOT returning a record
        # To maintain prior contract, we assume CSV columns: type,code,description,weight
        # Re-read as dicts via loader pattern:
        # pick an index and then map columns by a parallel headered read.
        # Simple approach: pick an index then map columns by parallel read using file_util.
        from datamimic_ce.domains.utils.dataset_path import dataset_path
        from datamimic_ce.utils.file_util import FileUtil

        file_path = dataset_path("insurance", f"products_{self._dataset}.csv", start=Path(__file__))
        _, rows = FileUtil.read_csv_having_weight_column(file_path, "weight")
        from typing import cast

        rows_dicts = cast(list[dict[str, object]], rows)
        # Avoid immediate repetition by type
        if self._last_product_type is not None and len(rows_dicts) > 1:
            pool = [row for row in rows_dicts if row.get("type") != self._last_product_type]
            pool_w = [float(str(row.get("weight", 1.0) or 1.0)) for row in pool]
            # Weighted choice over dict rows
            idx = self._rng.choices(range(len(pool)), weights=pool_w, k=1)[0]
            product_data = pool[idx]
        else:
            weights_all = [float(str(r.get("weight", 1.0) or 1.0)) for r in rows_dicts]
            idx = self._rng.choices(range(len(rows_dicts)), weights=weights_all, k=1)[0]
            product_data = rows_dicts[idx]
        _ptype = product_data.get("type")
        self._last_product_type = str(_ptype) if _ptype is not None else None

        return {"type": product_data["type"], "code": product_data["code"], "description": product_data["description"]}

    #  Centralize dataset I/O from model per SOC
    def pick_coverage_count(self, *, start_path: Path) -> int:
        from datamimic_ce.domains.utils.dataset_loader import load_weighted_values_try_dataset

        values, weights = load_weighted_values_try_dataset(
            "insurance", "product", "coverage_counts.csv", dataset=self._dataset, start=start_path
        )
        val = pick_one_weighted(self._rng, list(values), list(weights))
        try:
            return int(val)
        except (TypeError, ValueError):
            return 1
