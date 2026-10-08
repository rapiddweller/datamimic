from __future__ import annotations

from hashlib import sha256
from random import Random

import pytest

import datamimic_ce.domains.ecommerce.models.order as order_module
from datamimic_ce.domains.ecommerce.generators.order_generator import OrderGenerator
from datamimic_ce.domains.ecommerce.models.order import Order
from datamimic_ce.domains.shared.models.address import Address


def _fingerprint(rng: Random) -> str:
    return sha256(repr(rng.getstate()).encode()).hexdigest()


class _ScriptedRandom(Random):
    def __init__(self, values: list[float | Exception], events: list[str] | None = None) -> None:
        super().__init__(7)
        self.values = list(values)
        self.events = events if events is not None else []
        self.random_calls = 0

    def random(self) -> float:
        self.random_calls += 1
        self.events.append("random")
        value = self.values.pop(0)
        if isinstance(value, Exception):
            raise value
        return value

    def getrandbits(self, k: int) -> int:
        return super().getrandbits(k)


class _ObservedGenerator(OrderGenerator):
    def __init__(self, rng: Random, events: list[str] | None = None) -> None:
        self.rng_reads = 0
        self.address_reads = 0
        self.events = events if events is not None else []
        super().__init__(dataset="US", rng=rng)

    @property
    def rng(self) -> Random:
        self.rng_reads += 1
        self.events.append("rng")
        return self._rng

    @property
    def address_generator(self):
        self.address_reads += 1
        self.events.append("address_generator")
        return self._address_generator


@pytest.mark.parametrize(
    ("draw", "reuse"),
    [(0.0, True), (0.799999, True), (0.8, False), (0.999999, False)],
)
def test_generator_reuse_policy_uses_one_public_draw_and_strict_threshold(draw: float, reuse: bool) -> None:
    events: list[str] = []
    rng = _ScriptedRandom([draw], events)
    generator = _ObservedGenerator(rng, events)
    generator.rng_reads = 0
    events.clear()

    assert generator.should_reuse_shipping_address_for_billing() is reuse
    assert generator.rng_reads == 1
    assert rng.random_calls == 1
    assert events == ["rng", "random"]


@pytest.mark.parametrize("reuse", [True, False])
def test_billing_address_policy_runs_before_object_branch_and_keeps_address_lazy(reuse: bool) -> None:
    events: list[str] = []
    shipping = object()

    class CandidateGenerator(_ObservedGenerator):
        def should_reuse_shipping_address_for_billing(self) -> bool:
            events.append("reuse_policy")
            return reuse

    class EventOrder(Order):
        @property
        def shipping_address(self) -> Address:
            events.append("shipping_address")
            if not reuse:
                raise AssertionError("separate billing address evaluated shipping")
            return shipping  # type: ignore[return-value]

    generator = CandidateGenerator(_ScriptedRandom([0.99], events), events)
    row = next(iter(generator._address_generator._row_cache.values()))
    address_states = (
        _fingerprint(generator._address_generator.rng),
        *(
            _fingerprint(child.rng)
            for child in (
                row.city_generator,
                row.country_generator,
                row.phone_number_generator,
                row.street_name_generator,
            )
        ),
    )
    resolve_row = generator._address_generator.resolve_row

    def observed_resolve_row():
        events.append("resolve_row")
        return resolve_row()

    generator._address_generator.resolve_row = observed_resolve_row
    order = EventOrder(generator)
    generator.rng_reads = 0
    generator.address_reads = 0
    events.clear()

    billing = order.billing_address
    if reuse:
        assert billing is shipping
        assert events == ["reuse_policy", "shipping_address"]
        assert generator.address_reads == 0
    else:
        assert isinstance(billing, Address)
        assert billing.field_cache == {}
        assert events == ["reuse_policy", "address_generator", "resolve_row"]
        assert generator.address_reads == 1
        assert address_states == (
            _fingerprint(generator._address_generator.rng),
            *(
                _fingerprint(child.rng)
                for child in (
                    row.city_generator,
                    row.country_generator,
                    row.phone_number_generator,
                    row.street_name_generator,
                )
            ),
        )
    assert order.billing_address is billing


def test_billing_random_failure_is_uncached_and_retries() -> None:
    events: list[str] = []
    rng = _ScriptedRandom([RuntimeError("billing decision failed"), 0.1], events)
    generator = _ObservedGenerator(rng, events)
    order = Order(generator)
    shipping = Address(generator.address_generator)
    order.shipping_address = shipping
    generator.rng_reads = 0
    events.clear()

    with pytest.raises(RuntimeError, match="billing decision failed"):
        _ = order.billing_address
    assert "billing_address" not in order.field_cache

    assert order.billing_address is shipping
    assert order.billing_address is shipping
    assert rng.random_calls == 2
    assert generator.rng_reads == 2
    assert events == ["rng", "random", "rng", "random"]


def test_shipping_failure_after_reuse_decision_retries_opposite_branch() -> None:
    events: list[str] = []
    rng = _ScriptedRandom([0.1, 0.9], events)
    generator = _ObservedGenerator(rng, events)

    class FailingShippingOrder(Order):
        @property
        def shipping_address(self) -> Address:
            raise RuntimeError("shipping failed")

    order = FailingShippingOrder(generator)
    generator.rng_reads = 0
    events.clear()

    with pytest.raises(RuntimeError, match="shipping failed"):
        _ = order.billing_address
    assert "billing_address" not in order.field_cache
    assert "shipping_address" not in order.field_cache

    billing = order.billing_address
    assert isinstance(billing, Address)
    assert order.billing_address is billing
    assert "billing_address" in order.field_cache
    assert rng.random_calls == 2
    assert generator.rng_reads == 2
    assert events == ["rng", "random", "rng", "random", "address_generator"]


def test_address_construction_failure_after_separate_decision_retries_reuse_branch(monkeypatch) -> None:
    events: list[str] = []
    rng = _ScriptedRandom([0.9, 0.1], events)
    generator = _ObservedGenerator(rng, events)
    order = Order(generator)
    original_address = order_module.Address
    construction_calls = 0

    def fail_once(address_generator):
        nonlocal construction_calls
        construction_calls += 1
        if construction_calls == 1:
            raise RuntimeError("address construction failed")
        return original_address(address_generator)

    monkeypatch.setattr(order_module, "Address", fail_once)
    generator.rng_reads = 0
    events.clear()

    with pytest.raises(RuntimeError, match="address construction failed"):
        _ = order.billing_address
    assert "billing_address" not in order.field_cache
    assert "shipping_address" not in order.field_cache

    billing = order.billing_address
    assert billing is order.shipping_address
    assert isinstance(billing, original_address)
    assert order.billing_address is billing
    assert "billing_address" in order.field_cache
    assert rng.random_calls == 2
    assert generator.rng_reads == 2
    assert construction_calls == 2
    assert events == [
        "rng",
        "random",
        "address_generator",
        "rng",
        "random",
        "address_generator",
    ]


def test_cached_billing_address_survives_shipping_setter_replacement() -> None:
    rng = _ScriptedRandom([0.2])
    generator = _ObservedGenerator(rng)
    order = Order(generator)
    original_shipping = Address(generator.address_generator)
    order.shipping_address = original_shipping
    generator.rng_reads = 0

    billing = order.billing_address
    replacement_shipping = Address(generator.address_generator)
    order.shipping_address = replacement_shipping

    assert billing is original_shipping
    assert order.billing_address is billing
    assert order.shipping_address is replacement_shipping
    assert rng.random_calls == 1
    assert generator.rng_reads == 1


def test_billing_first_and_shipping_first_preserve_seeded_output_and_child_rng_state() -> None:
    billing_first_rng = Random(7)
    billing_first_generator = OrderGenerator(dataset="US", rng=billing_first_rng)
    billing_first = Order(billing_first_generator)
    row = next(iter(billing_first_generator.address_generator._row_cache.values()))
    assert _fingerprint(billing_first_rng) == (
        "c7c5d46d57c661574d539dbc75c63455927f4ffb2b1484af0da64d9030ecdde3"
    )
    assert _fingerprint(billing_first_generator.address_generator.rng) == (
        "cf8133534d72ca95c7901c37944d3cf5669d437ff5ff4cfbd424edab0a1557df"
    )
    billing = billing_first.billing_address
    assert billing is billing_first.shipping_address
    assert billing.full_address == "2nd Street 865, 75141 Hutchins, United States"
    assert _fingerprint(billing_first_rng) == (
        "96fed3bdd0e6eb987163f9be69002c4260594bef0c3dbab940723af7810cef07"
    )
    assert _fingerprint(billing_first_generator.address_generator.rng) == (
        "57d6c1fa74054fdde99d8809d79fe91566ddd3adf4950092720217a961582f0e"
    )
    assert _fingerprint(row.city_generator.rng) == (
        "dc74a661a66d736de423aef53d08fef0352d518faed025954b78073d0e160223"
    )

    shipping_first_rng = Random(7)
    shipping_first_generator = OrderGenerator(dataset="US", rng=shipping_first_rng)
    shipping_first = Order(shipping_first_generator)
    shipping = shipping_first.shipping_address
    billing = shipping_first.billing_address
    assert billing is shipping
    assert billing.full_address == "2nd Street 865, 75141 Hutchins, United States"
    assert _fingerprint(shipping_first_rng) == (
        "96fed3bdd0e6eb987163f9be69002c4260594bef0c3dbab940723af7810cef07"
    )
    assert _fingerprint(shipping_first_generator.address_generator.rng) == (
        "57d6c1fa74054fdde99d8809d79fe91566ddd3adf4950092720217a961582f0e"
    )
