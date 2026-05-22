import datetime as dt
import random
from pathlib import Path

from datamimic_ce.domains.common.generators.address_generator import AddressGenerator
from datamimic_ce.domains.domain_core.base_domain_generator import ClockAnchoredDomainGenerator
from datamimic_ce.domains.ecommerce.generators.product_generator import ProductGenerator
from datamimic_ce.domains.utils.dataset_loader import (
    load_weighted_values_try_dataset,
    pick_one_weighted,
    pick_weighted_from_headered_csv,
)
from datamimic_ce.domains.utils.dataset_path import dataset_path
from datamimic_ce.utils.file_util import FileUtil


class OrderGenerator(ClockAnchoredDomainGenerator):
    def __init__(
        self,
        dataset: str | None = None,
        rng: random.Random | None = None,
        reference_now: dt.datetime | None = None,
    ):
        super().__init__(dataset=dataset, rng=rng, reference_now=reference_now)
        self._product_generator = ProductGenerator(
            dataset=self._dataset,
            rng=self._derive_rng(),
        )
        # Share deterministic RNG to nested address fields so seeded orders replay.
        self._address_generator = AddressGenerator(
            dataset=self._dataset,
            rng=self._derive_rng(),
        )

    @property
    def product_generator(self) -> ProductGenerator:
        return self._product_generator

    @property
    def address_generator(self) -> AddressGenerator:
        return self._address_generator

    def _pick_from_weighted_csv(self, *path: str, value_col: str, weight_col: str = "weight") -> str:
        """Pick one value by weight from an ecommerce headered CSV (dataset-aware)."""
        file_path = dataset_path("ecommerce", *path, start=Path(__file__))
        return pick_weighted_from_headered_csv(self._rng, file_path, value_col=value_col, weight_col=weight_col)

    #  Centralize date generation; models stay pure and RNG boundaries are clear
    def generate_order_date(self) -> dt.datetime:
        from datamimic_ce.domains.common.literal_generators.datetime_generator import DateTimeGenerator

        now = self._reference_now
        min_dt = (now - dt.timedelta(days=365)).strftime("%Y-%m-%d %H:%M:%S")
        max_dt = now.strftime("%Y-%m-%d %H:%M:%S")
        val = DateTimeGenerator(min=min_dt, max=max_dt, random=True, rng=self._derive_rng()).generate()
        assert isinstance(val, dt.datetime)
        return val

    def get_order_status(self) -> str:
        return self._pick_from_weighted_csv(
            f"order_statuses_{self._dataset}.csv", value_col="status"
        )

    def get_payment_method(self) -> str:
        return self._pick_from_weighted_csv(
            f"payment_methods_{self._dataset}.csv", value_col="method"
        )

    def get_shipping_method(self) -> str:
        return self._pick_from_weighted_csv(
            f"shipping_methods_{self._dataset}.csv", value_col="method"
        )

    def get_currency_code(self) -> str:
        return self._pick_from_weighted_csv(
            f"currencies_{self._dataset}.csv", value_col="code"
        )

    def get_shipping_amount(self, shipping_method: str) -> float:
        # Load method rows, then pick bounds for the selected method
        file_path = dataset_path("ecommerce", f"shipping_methods_{self._dataset}.csv", start=Path(__file__))
        header_dict, rows = FileUtil.read_csv_to_dict_of_tuples_with_header(file_path, ",")
        idx_method = header_dict["method"]
        idx_min = header_dict["min_cost"]
        idx_max = header_dict["max_cost"]
        for row in rows:
            if row[idx_method] == shipping_method:
                try:
                    lo = float(row[idx_min])
                    hi = float(row[idx_max])
                except ValueError as e:
                    raise ValueError("Invalid shipping cost bounds") from e
                return round(self._rng.uniform(min(lo, hi), max(lo, hi)), 2)
        raise ValueError(
            f"Shipping method {shipping_method!r} not found in shipping_methods_{self._dataset}.csv"
        )

    def pick_coupon_prefix(self) -> str:
        values, weights = load_weighted_values_try_dataset(
            "ecommerce", "order", "coupon_prefixes.csv", dataset=self._dataset, start=Path(__file__)
        )
        return pick_one_weighted(self._rng, values, weights)

    def maybe_pick_note(self) -> str | None:
        if self._rng.random() >= 0.2:
            return None
        values, weights = load_weighted_values_try_dataset(
            "ecommerce", "order", "notes.csv", dataset=self._dataset, start=Path(__file__)
        )
        return pick_one_weighted(self._rng, values, weights)
