import datetime as dt
import random
from pathlib import Path

from datamimic_ce.domains.common.generators.address_generator import AddressGenerator
from datamimic_ce.domains.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.domains.ecommerce.generators.product_generator import ProductGenerator
from datamimic_ce.domains.utils.dataset_loader import load_weighted_values_try_dataset, pick_one_weighted


class OrderGenerator(BaseDomainGenerator):
    def __init__(self, dataset: str = "US", rng: random.Random | None = None):
        self._dataset = dataset.upper()  #  normalize for consistent dataset file suffixes
        self._rng: random.Random = rng or random.Random()
        self._product_generator = ProductGenerator(dataset=dataset, rng=self._rng)
        # Share deterministic RNG to nested address fields so seeded orders replay.
        self._address_generator = AddressGenerator(
            dataset=dataset,
            rng=self._derive_rng() if rng is not None else None,
        )

    @property
    def dataset(self) -> str:
        return self._dataset

    @property
    def product_generator(self) -> ProductGenerator:
        return self._product_generator

    @property
    def address_generator(self) -> AddressGenerator:
        return self._address_generator

    @property
    def rng(self) -> random.Random:
        return self._rng

    def _derive_rng(self) -> random.Random:
        # Spawn deterministic child RNGs so seeded orders replay without cross-coupling randomness.
        return random.Random(self._rng.randrange(2**63)) if isinstance(self._rng, random.Random) else random.Random()

    #  Centralize date generation; models stay pure and RNG boundaries are clear
    def generate_order_date(self) -> dt.datetime:
        from datamimic_ce.domains.common.literal_generators.datetime_generator import DateTimeGenerator

        now = dt.datetime.now()
        min_dt = (now - dt.timedelta(days=365)).strftime("%Y-%m-%d %H:%M:%S")
        max_dt = now.strftime("%Y-%m-%d %H:%M:%S")
        val = DateTimeGenerator(min=min_dt, max=max_dt, random=True, rng=self._derive_rng()).generate()
        assert isinstance(val, dt.datetime)
        return val

    def get_order_status(self) -> str:
        from datamimic_ce.domains.utils.dataset_path import dataset_path
        from datamimic_ce.utils.file_util import FileUtil

        file_path = dataset_path("ecommerce", f"order_statuses_{self._dataset}.csv", start=Path(__file__))
        header, rows = FileUtil.read_csv_to_dict_of_tuples_with_header(file_path, ",")
        w_idx = header.get("weight")
        v_idx = header.get("status")
        if w_idx is None or v_idx is None:
            # fallback to headerless interpretation if structure unexpected
            values, weights = load_weighted_values_try_dataset(
                "ecommerce", "order_statuses.csv", dataset=self._dataset, start=Path(__file__)
            )
            return pick_one_weighted(self._rng, values, weights)
        choice = self._rng.choices(rows, weights=[float(r[w_idx]) for r in rows], k=1)[0]
        return choice[v_idx]

    def get_payment_method(self) -> str:
        from datamimic_ce.domains.utils.dataset_path import dataset_path
        from datamimic_ce.utils.file_util import FileUtil

        file_path = dataset_path("ecommerce", f"payment_methods_{self._dataset}.csv", start=Path(__file__))
        header, rows = FileUtil.read_csv_to_dict_of_tuples_with_header(file_path, ",")
        w_idx = header.get("weight")
        v_idx = header.get("method")
        if w_idx is None or v_idx is None:
            values, weights = load_weighted_values_try_dataset(
                "ecommerce", "payment_methods.csv", dataset=self._dataset, start=Path(__file__)
            )
            return pick_one_weighted(self._rng, values, weights)
        choice = self._rng.choices(rows, weights=[float(r[w_idx]) for r in rows], k=1)[0]
        return choice[v_idx]

    def get_shipping_method(self) -> str:
        from datamimic_ce.domains.utils.dataset_path import dataset_path
        from datamimic_ce.utils.file_util import FileUtil

        file_path = dataset_path("ecommerce", f"shipping_methods_{self._dataset}.csv", start=Path(__file__))
        header, rows = FileUtil.read_csv_to_dict_of_tuples_with_header(file_path, ",")
        w_idx = header.get("weight")
        v_idx = header.get("method")
        if w_idx is None or v_idx is None:
            values, weights = load_weighted_values_try_dataset(
                "ecommerce", "shipping_methods.csv", dataset=self._dataset, start=Path(__file__)
            )
            return pick_one_weighted(self._rng, values, weights)
        choice = self._rng.choices(rows, weights=[float(r[w_idx]) for r in rows], k=1)[0]
        return choice[v_idx]

    def get_currency_code(self) -> str:
        from datamimic_ce.domains.utils.dataset_path import dataset_path
        from datamimic_ce.utils.file_util import FileUtil

        file_path = dataset_path("ecommerce", f"currencies_{self._dataset}.csv", start=Path(__file__))
        header, rows = FileUtil.read_csv_to_dict_of_tuples_with_header(file_path, ",")
        w_idx = header.get("weight")
        v_idx = header.get("code")
        if w_idx is None or v_idx is None:
            values, weights = load_weighted_values_try_dataset(
                "ecommerce", "currencies.csv", dataset=self._dataset, start=Path(__file__)
            )
            return pick_one_weighted(self._rng, values, weights)
        choice = self._rng.choices(rows, weights=[float(r[w_idx]) for r in rows], k=1)[0]
        return choice[v_idx]

    def get_shipping_amount(self, shipping_method: str) -> float:
        # Load method rows, then pick bounds for the selected method
        from datamimic_ce.domains.utils.dataset_path import dataset_path
        from datamimic_ce.utils.file_util import FileUtil

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
        # If not found, default minimal cost
        return 0.0

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
