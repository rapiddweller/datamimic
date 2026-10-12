from __future__ import annotations

from hashlib import sha256
from random import Random

import pytest

from datamimic_ce.domains.ecommerce.generators.order_generator import OrderGenerator
from datamimic_ce.domains.ecommerce.models.order import Order
from datamimic_ce.domains.shared.literal_generators.primitives.string_generator import StringGenerator


def _fingerprint(rng: Random) -> str:
    return sha256(repr(rng.getstate()).encode()).hexdigest()


class _ObservedGenerator(OrderGenerator):
    def __init__(self, rng: Random, events: list[object] | None = None) -> None:
        self.rng_reads = 0
        self.events = events
        self.prefixes = ["DEAL"]
        super().__init__(dataset="US", rng=rng)

    @property
    def rng(self) -> Random:
        self.rng_reads += 1
        if self.events is not None:
            self.events.append("rng")
        return self._rng

    def pick_coupon_prefix(self) -> str:
        if self.events is not None:
            self.events.append("prefix")
        return self.prefixes.pop(0)


def test_coupon_code_keeps_discount_gate_and_caches_none_for_zero_or_negative() -> None:
    for amount in (0.0, -0.01):
        rng = Random(19)
        generator = _ObservedGenerator(rng)
        order = Order(generator)
        order._field_cache["discount_amount"] = amount

        assert order.coupon_code is None
        state = rng.getstate()
        assert order.coupon_code is None
        assert rng.getstate() == state
        assert generator.rng_reads == 0


def test_generator_coupon_code_orders_prefix_before_rng_and_regex_and_keeps_leading_zeroes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[object] = []
    rng = Random(19)
    generator = _ObservedGenerator(rng, events)
    regex_calls: list[tuple[str, Random]] = []

    def regex_code(pattern: str, *, rng: Random) -> str:
        events.append("regex")
        regex_calls.append((pattern, rng))
        return "0000A9"

    monkeypatch.setattr(StringGenerator, "rnd_str_from_regex", staticmethod(regex_code))

    assert generator.generate_coupon_code() == "DEAL0000A9"
    assert events == ["prefix", "rng", "regex"]
    assert regex_calls == [("[A-Z0-9]{6}", rng)]
    assert generator.rng_reads == 1


def test_positive_coupon_code_is_cached_without_reselecting_prefix_or_reading_rng(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[object] = []
    rng = Random(19)
    generator = _ObservedGenerator(rng, events)
    order = Order(generator)
    order._field_cache["discount_amount"] = 1.0
    monkeypatch.setattr(
        StringGenerator,
        "rnd_str_from_regex",
        staticmethod(lambda pattern, *, rng: "ABC123"),
    )

    assert order.coupon_code == "DEALABC123"
    state = rng.getstate()
    assert order.coupon_code == "DEALABC123"
    assert rng.getstate() == state
    assert events == ["prefix", "rng"]
    assert generator.rng_reads == 1


def test_coupon_prefix_failure_prevents_regex_and_leaves_coupon_uncached(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    generator = _ObservedGenerator(Random(19))
    order = Order(generator)
    order._field_cache["discount_amount"] = 1.0
    calls = 0
    regex_calls = 0

    def prefix() -> str:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("scripted prefix failure")
        return "OK"

    def regex_code(pattern: str, *, rng: Random) -> str:
        nonlocal regex_calls
        regex_calls += 1
        assert pattern == "[A-Z0-9]{6}"
        return "ABC123"

    monkeypatch.setattr(generator, "pick_coupon_prefix", prefix)
    monkeypatch.setattr(StringGenerator, "rnd_str_from_regex", staticmethod(regex_code))

    with pytest.raises(RuntimeError, match="scripted prefix failure"):
        _ = order.coupon_code
    assert "coupon_code" not in order.field_cache
    assert order.discount_amount == 1.0
    assert regex_calls == 0

    assert order.coupon_code == "OKABC123"
    assert calls == 2
    assert regex_calls == 1


def test_coupon_regex_failure_retries_prefix_and_keeps_discount_cached(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    generator = _ObservedGenerator(Random(19))
    generator.prefixes = ["OLD", "NEW"]
    order = Order(generator)
    order._field_cache["discount_amount"] = 1.0
    regex_calls = 0

    def regex_code(pattern: str, *, rng: Random) -> str:
        nonlocal regex_calls
        regex_calls += 1
        if regex_calls == 1:
            raise RuntimeError("scripted regex failure")
        return "000001"

    monkeypatch.setattr(StringGenerator, "rnd_str_from_regex", staticmethod(regex_code))

    with pytest.raises(RuntimeError, match="scripted regex failure"):
        _ = order.coupon_code
    assert "coupon_code" not in order.field_cache
    assert order.discount_amount == 1.0

    assert order.coupon_code == "NEW000001"
    assert regex_calls == 2
    assert generator.rng_reads == 2


def test_coupon_code_delegates_final_code_construction_to_generator() -> None:
    events: list[object] = []

    class CandidateGenerator(OrderGenerator):
        def pick_coupon_prefix(self) -> str:
            events.append("prefix")
            return "DEAL"

        def generate_coupon_code(self) -> str:
            events.append("generate_coupon_code")
            return "PROMO000001"

    order = Order(CandidateGenerator(dataset="US", rng=Random(19)))
    order._field_cache["discount_amount"] = 0.01

    assert order.coupon_code == "PROMO000001"
    assert events == ["generate_coupon_code"]


@pytest.mark.parametrize(
    (
        "seed",
        "coupon",
        "discount",
        "rng_after",
        "product_rng_after",
        "rng_before",
        "product_rng_before",
    ),
    [
        (
            431,
            None,
            0.0,
            "75dd86564b94d76a5e4f95c3405595ccc0d9bef5c4002b26648275fdcae874df",
            "71ceedb82a52ee7f34cd1a3ec76965bdbbf314239d0ec721a189b3ff9a9026a5",
            "7209cf7ecf7d2e7939971861054d43b0193efb2c38f5ce5c141f724fb9ecf01b",
            "71ceedb82a52ee7f34cd1a3ec76965bdbbf314239d0ec721a189b3ff9a9026a5",
        ),
        (
            7,
            "SPECIALCF10EP",
            399.5,
            "5bd42a63a8629c8ab85fcc55ac6a3d82d286b723eaa06174324abd2eb757eaac",
            "09d55305fcabde69b96c4d4b1fa2a3105ef9322ab13791c0760b85ffb9a466a6",
            "c7c5d46d57c661574d539dbc75c63455927f4ffb2b1484af0da64d9030ecdde3",
            "728b4403257f3d8998f207d5359d462cbb534ebc1e92a8ed283562e1bf3a04e2",
        ),
    ],
)
def test_coupon_first_and_discount_first_preserve_seeded_branch_outputs_and_states(
    seed: int,
    coupon: str | None,
    discount: float,
    rng_after: str,
    product_rng_after: str,
    rng_before: str,
    product_rng_before: str,
) -> None:
    coupon_first_rng = Random(seed)
    coupon_first_generator = OrderGenerator(dataset="US", rng=coupon_first_rng)
    coupon_first = Order(coupon_first_generator)
    initial_state = _fingerprint(coupon_first_rng)
    initial_product_state = _fingerprint(coupon_first_generator.product_generator.rng)
    assert initial_state == rng_before
    assert initial_product_state == product_rng_before
    assert coupon_first.coupon_code == coupon
    assert _fingerprint(coupon_first_rng) == rng_after
    assert _fingerprint(coupon_first_generator.product_generator.rng) == product_rng_after
    assert coupon_first.discount_amount == discount

    discount_first_rng = Random(seed)
    discount_first_generator = OrderGenerator(dataset="US", rng=discount_first_rng)
    discount_first = Order(discount_first_generator)
    assert _fingerprint(discount_first_rng) == initial_state
    assert _fingerprint(discount_first_generator.product_generator.rng) == initial_product_state
    assert discount_first.discount_amount == discount
    assert discount_first.coupon_code == coupon
    assert _fingerprint(discount_first_rng) == rng_after
    assert _fingerprint(discount_first_generator.product_generator.rng) == product_rng_after
