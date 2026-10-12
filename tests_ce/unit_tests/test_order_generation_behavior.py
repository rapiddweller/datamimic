from __future__ import annotations

from hashlib import sha256
from random import Random

import pytest

from datamimic_ce.domains.ecommerce.generators.order_generator import OrderGenerator
from datamimic_ce.domains.ecommerce.generators.product_generator import ProductGenerator
from datamimic_ce.domains.ecommerce.models.order import Order
from datamimic_ce.domains.ecommerce.models.product import Product


def _fingerprint(rng: Random) -> str:
    return sha256(repr(rng.getstate()).encode()).hexdigest()


class _UniformRandom(Random):
    def __init__(
        self,
        value: float = 0.1,
        *,
        error_once: bool = False,
        events: list[str] | None = None,
    ) -> None:
        super().__init__(7)
        self.value = value
        self.error_once = error_once
        self.events = events
        self.uniform_calls: list[tuple[float, float]] = []

    def uniform(self, a: float, b: float) -> float:
        self.uniform_calls.append((a, b))
        if self.events is not None:
            self.events.append("uniform")
        if self.error_once:
            self.error_once = False
            raise RuntimeError("scripted tax draw failure")
        return self.value


class _ObservedOrderGenerator(OrderGenerator):
    def __init__(self, rng: Random, events: list[str] | None = None) -> None:
        self.rng_reads = 0
        self.events = events
        super().__init__(dataset="US", rng=rng)

    @property
    def rng(self) -> Random:
        self.rng_reads += 1
        if self.events is not None:
            self.events.append("rng")
        return self._rng


def test_tax_amount_sums_prices_before_one_public_rng_draw_and_rounds() -> None:
    events: list[str] = []

    class Item:
        def __init__(self, price: float) -> None:
            self._price = price

        @property
        def price(self) -> float:
            events.append(f"price:{self._price}")
            return self._price

    rng = _UniformRandom(0.1, events=events)
    generator = _ObservedOrderGenerator(rng, events)
    order = Order(generator)
    assert events == []
    assert generator.rng_reads == 0
    order.product_list = [Item(1.25), Item(2.50)]  # type: ignore[list-item]
    generator.rng_reads = 0

    assert order.tax_amount == 0.38
    assert events == ["price:1.25", "price:2.5", "rng", "uniform"]
    assert generator.rng_reads == 1
    assert rng.uniform_calls == [(0.05, 0.12)]
    state = rng.getstate()
    assert order.tax_amount == 0.38
    assert rng.getstate() == state
    assert generator.rng_reads == 1
    assert rng.uniform_calls == [(0.05, 0.12)]


def test_tax_amount_empty_list_still_draws_and_zero_subtotal_stays_zero() -> None:
    rng = _UniformRandom(0.12)
    generator = _ObservedOrderGenerator(rng)
    order = Order(generator)
    order.product_list = []
    generator.rng_reads = 0

    assert order.tax_amount == 0.0
    assert generator.rng_reads == 1
    assert rng.uniform_calls == [(0.05, 0.12)]


def test_tax_amount_price_failure_precedes_rng_and_retries() -> None:
    rng = _UniformRandom()
    generator = _ObservedOrderGenerator(rng)
    order = Order(generator)

    class FailingPrice:
        calls = 0

        @property
        def price(self) -> float:
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("scripted price failure")
            return 10.0

    item = FailingPrice()
    order.product_list = [item]  # type: ignore[list-item]
    generator.rng_reads = 0

    with pytest.raises(RuntimeError, match="scripted price failure"):
        _ = order.tax_amount
    assert "tax_amount" not in order.field_cache
    assert generator.rng_reads == 0
    assert rng.uniform_calls == []

    assert order.tax_amount == 1.0
    assert generator.rng_reads == 1
    assert rng.uniform_calls == [(0.05, 0.12)]


def test_tax_amount_rng_failure_is_uncached_and_retry_succeeds() -> None:
    rng = _UniformRandom(error_once=True)
    generator = _ObservedOrderGenerator(rng)
    order = Order(generator)
    order.product_list = []
    generator.rng_reads = 0

    with pytest.raises(RuntimeError, match="scripted tax draw failure"):
        _ = order.tax_amount
    assert "tax_amount" not in order.field_cache
    assert generator.rng_reads == 1
    assert rng.uniform_calls == [(0.05, 0.12)]

    assert order.tax_amount == 0.0
    assert generator.rng_reads == 2
    assert rng.uniform_calls == [(0.05, 0.12), (0.05, 0.12)]


def test_orders_sharing_generator_cache_tax_independently() -> None:
    rng = _UniformRandom(0.1)
    generator = _ObservedOrderGenerator(rng)
    first = Order(generator)
    second = Order(generator)
    first.product_list = []
    second.product_list = []

    assert first.tax_amount == 0.0
    assert first.tax_amount == 0.0
    assert second.tax_amount == 0.0
    assert rng.uniform_calls == [(0.05, 0.12), (0.05, 0.12)]


def test_tax_amount_delegates_subtotal_to_generator() -> None:
    class CandidateGenerator(OrderGenerator):
        def generate_tax_amount(self, subtotal: float) -> float:
            assert subtotal == 12.5
            return 4.25

    order = Order(CandidateGenerator(dataset="US", rng=Random(7)))
    order.product_list = [type("Item", (), {"price": 12.5})()]  # type: ignore[list-item]

    assert order.tax_amount == 4.25


def test_tax_first_and_total_first_preserve_seeded_order_and_child_state() -> None:
    tax_first_rng = Random(431)
    tax_first_generator = OrderGenerator(dataset="US", rng=tax_first_rng)
    tax_first = Order(tax_first_generator)
    assert _fingerprint(tax_first_rng) == "7209cf7ecf7d2e7939971861054d43b0193efb2c38f5ce5c141f724fb9ecf01b"
    assert _fingerprint(tax_first_generator.product_generator.rng) == (
        "71ceedb82a52ee7f34cd1a3ec76965bdbbf314239d0ec721a189b3ff9a9026a5"
    )
    assert tax_first.tax_amount == 50.12
    assert _fingerprint(tax_first_rng) == "9a6e9643d34a84c99bb983daa11b6a0105e1b3c566ef9d5068f34891469d34e2"
    assert _fingerprint(tax_first_generator.product_generator.rng) == (
        "f978d39ae5b027d0c20cbe38817b8f31e993129aa9d21e28d7599b53ba1ec3a2"
    )
    assert tax_first.total_amount == 1066.4
    assert _fingerprint(tax_first_rng) == "a42cd92780300077c09ee680b0b913500495f84fa976107bb9738c85150df6b1"

    total_first_rng = Random(431)
    total_first_generator = OrderGenerator(dataset="US", rng=total_first_rng)
    total_first = Order(total_first_generator)
    assert _fingerprint(total_first_rng) == "7209cf7ecf7d2e7939971861054d43b0193efb2c38f5ce5c141f724fb9ecf01b"
    assert total_first.total_amount == 1066.4
    assert _fingerprint(total_first_rng) == "a42cd92780300077c09ee680b0b913500495f84fa976107bb9738c85150df6b1"
    assert _fingerprint(total_first_generator.product_generator.rng) == (
        "f978d39ae5b027d0c20cbe38817b8f31e993129aa9d21e28d7599b53ba1ec3a2"
    )
    assert total_first.tax_amount == 50.12
    assert _fingerprint(total_first_rng) == "a42cd92780300077c09ee680b0b913500495f84fa976107bb9738c85150df6b1"


class _CountRandom(Random):
    def __init__(self, values: list[int | Exception], events: list[object]) -> None:
        super().__init__(31)
        self.values = values
        self.events = events

    def randint(self, a: int, b: int) -> int:
        self.events.append(("randint", a, b))
        value = self.values.pop(0)
        if isinstance(value, Exception):
            raise value
        return value


class _CountOrderGenerator(OrderGenerator):
    def __init__(self, rng: Random, events: list[object]) -> None:
        self.events = events
        self.rng_reads = 0
        super().__init__(dataset="US", rng=rng)

    @property
    def rng(self) -> Random:
        self.rng_reads += 1
        self.events.append("rng")
        return self._rng

    @property
    def product_generator(self) -> ProductGenerator:
        self.events.append("child_lookup")
        return self._product_generator


@pytest.mark.parametrize("count", [1, 10])
def test_product_list_count_uses_inclusive_one_to_ten_bounds_and_caches(count: int) -> None:
    events: list[object] = []
    generator = _CountOrderGenerator(_CountRandom([count], events), events)
    order = Order(generator)

    products = order.product_list
    assert len(products) == count
    assert len({id(product) for product in products}) == count
    assert events == ["rng", ("randint", 1, 10), *(["child_lookup"] * count)]
    assert order.product_list is products
    assert events == ["rng", ("randint", 1, 10), *(["child_lookup"] * count)]


def test_product_list_count_failure_does_not_lookup_children_and_retries() -> None:
    events: list[object] = []
    generator = _CountOrderGenerator(
        _CountRandom([RuntimeError("scripted count failure"), 1], events), events
    )
    order = Order(generator)

    with pytest.raises(RuntimeError, match="scripted count failure"):
        _ = order.product_list
    assert "product_list" not in order.field_cache
    assert events == ["rng", ("randint", 1, 10)]

    assert len(order.product_list) == 1
    assert events == ["rng", ("randint", 1, 10), "rng", ("randint", 1, 10), "child_lookup"]


def test_product_list_child_lookup_failure_discards_partial_list_and_retries_count() -> None:
    events: list[object] = []

    class FailingChildGenerator(_CountOrderGenerator):
        child_lookups = 0

        @property
        def product_generator(self) -> ProductGenerator:
            self.child_lookups += 1
            events.append("child_lookup")
            if self.child_lookups == 2:
                raise RuntimeError("scripted child lookup failure")
            return self._product_generator

    generator = FailingChildGenerator(_CountRandom([2, 2], events), events)
    order = Order(generator)

    with pytest.raises(RuntimeError, match="scripted child lookup failure"):
        _ = order.product_list
    assert "product_list" not in order.field_cache
    assert events == ["rng", ("randint", 1, 10), "child_lookup", "child_lookup"]

    products = order.product_list
    assert len(products) == 2
    assert events == [
        "rng",
        ("randint", 1, 10),
        "child_lookup",
        "child_lookup",
        "rng",
        ("randint", 1, 10),
        "child_lookup",
        "child_lookup",
    ]


def test_product_list_setter_bypasses_count_draw_and_child_lookup() -> None:
    events: list[object] = []
    generator = _CountOrderGenerator(_CountRandom([1], events), events)
    order = Order(generator)
    supplied = [Product(generator._product_generator)]

    order.product_list = supplied

    assert order.product_list is supplied
    assert events == []


def test_product_list_setter_replaces_generated_list_without_more_draws_or_lookups() -> None:
    events: list[object] = []
    generator = _CountOrderGenerator(_CountRandom([2], events), events)
    order = Order(generator)
    _ = order.product_list
    before_replacement = events.copy()
    replacement: list[Product] = []

    order.product_list = replacement

    assert order.product_list is replacement
    assert events == before_replacement


def test_shared_generator_orders_keep_mutable_product_lists_independent() -> None:
    events: list[object] = []
    generator = _CountOrderGenerator(_CountRandom([1, 1], events), events)
    first = Order(generator)
    second = Order(generator)

    first_products = first.product_list
    second_products = second.product_list
    first_products.append(Product(generator._product_generator))

    assert first.product_list is first_products
    assert second.product_list is second_products
    assert len(first_products) == 2
    assert len(second_products) == 1


def test_product_list_construction_does_not_draw_child_values_or_populate_product_cache() -> None:
    events: list[object] = []
    generator = _CountOrderGenerator(_CountRandom([3], events), events)
    child_rng = generator.product_generator.rng
    before = _fingerprint(child_rng)
    order = Order(generator)

    products = order.product_list

    assert len(products) == 3
    assert _fingerprint(child_rng) == before
    assert all(product.field_cache == {} for product in products)


def test_product_list_delegates_count_to_order_generator() -> None:
    events: list[object] = []

    class CandidateGenerator(_CountOrderGenerator):
        def generate_product_count(self) -> int:
            events.append("generate_product_count")
            return 1

    generator = CandidateGenerator(_CountRandom([], events), events)
    order = Order(generator)

    assert len(order.product_list) == 1
    assert events == ["generate_product_count", "child_lookup"]
