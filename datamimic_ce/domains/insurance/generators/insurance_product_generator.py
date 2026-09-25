import random
from pathlib import Path

from datamimic_ce.domains.domain_core.base_domain_generator import DatasetAwareDomainGenerator
from datamimic_ce.domains.insurance.generators.insurance_coverage_generator import InsuranceCoverageGenerator
from datamimic_ce.domains.shared.utils.dataset_loader import pick_one_weighted, read_weighted_records


class InsuranceProductGenerator(DatasetAwareDomainGenerator):
    """Generator for insurance product data."""

    def __init__(
        self,
        dataset: str | None = None,
        rng: random.Random | None = None,
    ):
        """Initialize the insurance product generator.

        Args:
            dataset: The country code to use for data generation
            rng: Optional seeded random instance for deterministic output.
        """
        super().__init__(dataset=dataset, rng=rng)
        self._insurance_coverage_generator = InsuranceCoverageGenerator(
            dataset=self._dataset,
            rng=self._derive_rng(),
        )
        self._last_product_type: str | None = None

    @property
    def insurance_coverage_generator(self) -> InsuranceCoverageGenerator:
        return self._insurance_coverage_generator

    def get_random_product(self) -> dict[str, str]:
        # values are expected to be serialized dict-like fields or codes; we prefer SPOT returning a record
        # To maintain prior contract, we assume CSV columns: type,code,description,weight
        # Re-read as dicts via loader pattern:
        # Pick an index, then map columns from the headered rows.
        from datamimic_ce.domains.shared.utils.dataset_path import dataset_path

        file_path = dataset_path("insurance", f"products_{self._dataset}.csv", start=Path(__file__))
        _, rows_dicts = read_weighted_records(file_path, "weight")
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
        from datamimic_ce.domains.shared.utils.dataset_loader import load_weighted_values_try_dataset

        values, weights = load_weighted_values_try_dataset(
            "insurance", "product", "coverage_counts.csv", dataset=self._dataset, start=start_path
        )
        val = pick_one_weighted(self._rng, list(values), list(weights))
        try:
            return int(val)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Non-integer coverage count {val!r} in coverage_counts_{self._dataset}.csv") from e
