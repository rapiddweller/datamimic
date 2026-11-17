import random
from pathlib import Path

from datamimic_ce.domains.domain_core.base_domain_generator import DatasetAwareDomainGenerator
from datamimic_ce.domains.domain_core.runtime.rng_uuid import uuid4_from_random
from datamimic_ce.domains.insurance.generators.insurance_coverage_generator import InsuranceCoverageGenerator
from datamimic_ce.domains.shared.datasets.loader import pick_one_weighted, read_weighted_records


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

    def generate_id_candidate(self) -> str:
        return uuid4_from_random(self.rng)

    @property
    def insurance_coverage_generator(self) -> InsuranceCoverageGenerator:
        return self._insurance_coverage_generator

    def get_random_product(self) -> dict[str, str]:
        # values are expected to be serialized dict-like fields or codes; we prefer SPOT returning a record
        # To maintain prior contract, we assume CSV columns: type,code,description,weight
        # Re-read as dicts via loader pattern:
        # Pick an index, then map columns from the headered rows.
        from datamimic_ce.domains.domain_core.datasets.path import dataset_path

        file_path = dataset_path("insurance", f"products_{self._dataset}.csv", start=Path(__file__))
        _, rows_dicts = read_weighted_records(file_path, "weight")
        weights = [float(str(r.get("weight", 1.0) or 1.0)) for r in rows_dicts]
        product_data = self._rng.choices(rows_dicts, weights=weights, k=1)[0]

        return {"type": product_data["type"], "code": product_data["code"], "description": product_data["description"]}

    #  Centralize dataset I/O from model per SOC
    def pick_coverage_count(self, *, start_path: Path) -> int:
        from datamimic_ce.domains.shared.datasets.loader import load_weighted_values_try_dataset

        values, weights = load_weighted_values_try_dataset(
            "insurance", "product", "coverage_counts.csv", dataset=self._dataset, start=start_path
        )
        val = pick_one_weighted(self._rng, list(values), list(weights))
        try:
            return int(val)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Non-integer coverage count {val!r} in coverage_counts_{self._dataset}.csv") from e
