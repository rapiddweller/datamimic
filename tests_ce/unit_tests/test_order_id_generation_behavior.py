from __future__ import annotations

from hashlib import sha256
from random import Random

import pytest

from datamimic_ce.domains.ecommerce.generators.order_generator import OrderGenerator
from datamimic_ce.domains.ecommerce.models.order import Order
from datamimic_ce.domains.ecommerce.services.order_service import OrderService
from datamimic_ce.domains.shared.literal_generators.identity.keys import prefixed_id_generator
from datamimic_ce.domains.shared.literal_generators.primitives.string_generator import StringGenerator


def _fingerprint(rng: Random) -> str:
    return sha256(repr(rng.getstate()).encode()).hexdigest()


class _ObservedOrderGenerator(OrderGenerator):
    def __init__(self, rng: Random) -> None:
        self.rng_reads = 0
        super().__init__(dataset="US", rng=rng)

    @property
    def rng(self) -> Random:
        self.rng_reads += 1
        return self._rng


def test_order_construction_is_lazy_and_id_candidates_delegate_to_generator() -> None:
    class CandidateGenerator(_ObservedOrderGenerator):
        def generate_order_id_candidate(self) -> str:
            return "ORDORDER001"

        def generate_user_id(self) -> str:
            return "USERUSER001"

    generator = CandidateGenerator(Random(902))
    order = Order(generator)

    assert order.field_cache == {}
    assert generator.rng_reads == 0
    assert order.order_id == "ORDORDER001"
    assert order.user_id == "USERUSER001"
    assert generator.rng_reads == 0
    assert order.order_id == "ORDORDER001"
    assert order.user_id == "USERUSER001"


def test_order_and_user_ids_use_call_time_prefixed_helper_with_exact_arguments(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, str, str, Random]] = []

    class RecordingPrefixedIdGenerator:
        def __init__(self, prefix: str, pattern: str, separator: str, rng: Random) -> None:
            calls.append((prefix, pattern, separator, rng))

        def generate(self) -> str:
            return f"{calls[-1][0]}GENERATE"

    monkeypatch.setattr(prefixed_id_generator, "PrefixedIdGenerator", RecordingPrefixedIdGenerator)
    rng = Random(902)
    generator = _ObservedOrderGenerator(rng)
    order = Order(generator)
    initial_state = rng.getstate()

    assert order.field_cache == {}
    assert rng.getstate() == initial_state
    assert generator.rng_reads == 0
    assert order.order_id == "ORDGENERATE"
    assert calls == [("ORD", "[A-Z0-9]{8}", "", rng)]
    assert generator.rng_reads == 1
    assert order.user_id == "USERGENERATE"
    assert calls[-1] == ("USER", "[A-Z0-9]{8}", "", rng)
    assert generator.rng_reads == 2
    assert order.order_id == "ORDGENERATE"
    assert order.user_id == "USERGENERATE"
    assert len(calls) == 2
    assert generator.rng_reads == 2


def test_order_id_is_claimed_after_candidate_generation_but_user_id_is_never_claimed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []

    def body(pattern: str, *, rng: Random) -> str:
        events.append("candidate")
        assert pattern == "[A-Z0-9]{8}"
        return "AAAAAAAA"

    monkeypatch.setattr(StringGenerator, "rnd_str_from_regex", staticmethod(body))
    order = Order(OrderGenerator(dataset="US", rng=Random(18)))
    original_claim = order._claim_identifier

    def observed_claim(name: str, value: str) -> str:
        events.append(f"claim:{name}")
        return original_claim(name, value)

    monkeypatch.setattr(order, "_claim_identifier", observed_claim)
    assert order.order_id == "ORDAAAAAAAA"
    assert events == ["candidate", "claim:order_id"]

    def forbidden_claim(name: str, value: str) -> str:
        raise AssertionError(f"unexpected claim for {name}={value}")

    monkeypatch.setattr(order, "_claim_identifier", forbidden_claim)
    assert order.user_id == "USERAAAAAAAA"


def test_shared_generator_orders_allow_duplicate_unbound_user_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0

    def fixed_body(pattern: str, *, rng: Random) -> str:
        nonlocal calls
        calls += 1
        assert pattern == "[A-Z0-9]{8}"
        return "AAAAAAAA"

    monkeypatch.setattr(StringGenerator, "rnd_str_from_regex", staticmethod(fixed_body))
    generator = _ObservedOrderGenerator(Random(19))
    first = Order(generator)
    second = Order(generator)

    assert first.user_id == second.user_id == "USERAAAAAAAA"
    assert first.user_id == "USERAAAAAAAA"
    assert second.user_id == "USERAAAAAAAA"
    assert calls == 2
    assert generator.rng_reads == 2


def test_bound_orders_allow_duplicate_user_ids_without_identifier_claim(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0

    def fixed_body(pattern: str, *, rng: Random) -> str:
        nonlocal calls
        calls += 1
        assert pattern == "[A-Z0-9]{8}"
        return "AAAAAAAA"

    monkeypatch.setattr(StringGenerator, "rnd_str_from_regex", staticmethod(fixed_body))
    orders = OrderService(dataset="US", rng=Random(19)).generate_batch(2)

    assert [order.user_id for order in orders] == ["USERAAAAAAAA", "USERAAAAAAAA"]
    assert calls == 2


def test_bound_order_id_collision_is_claimed_without_candidate_redraw(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0

    def repeated_body(pattern: str, *, rng: Random) -> str:
        nonlocal calls
        calls += 1
        assert pattern == "[A-Z0-9]{8}"
        return "00000000"

    monkeypatch.setattr(StringGenerator, "rnd_str_from_regex", staticmethod(repeated_body))
    service = OrderService(dataset="US", rng=Random(19))
    orders = service.generate_batch(2)

    assert [order.order_id for order in orders] == ["ORD00000000", "ORD00000001"]
    assert calls == 2


def test_order_id_generation_failure_is_uncached_and_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    original = StringGenerator.rnd_str_from_regex
    calls = 0

    def fail_once(pattern: str, *, rng: Random) -> str:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("scripted order id generation failure")
        return original(pattern, rng=rng)

    monkeypatch.setattr(StringGenerator, "rnd_str_from_regex", staticmethod(fail_once))
    order = Order(OrderGenerator(dataset="US", rng=Random(902)))

    with pytest.raises(RuntimeError, match="scripted order id generation failure"):
        _ = order.order_id
    assert "order_id" not in order.field_cache

    assert order.order_id.startswith("ORD")
    assert order.order_id == order.field_cache["order_id"]
    assert calls == 2


def test_user_id_generation_failure_is_uncached_and_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    original = StringGenerator.rnd_str_from_regex
    calls = 0

    def fail_once(pattern: str, *, rng: Random) -> str:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("scripted user id generation failure")
        return original(pattern, rng=rng)

    monkeypatch.setattr(StringGenerator, "rnd_str_from_regex", staticmethod(fail_once))
    order = Order(OrderGenerator(dataset="US", rng=Random(902)))

    with pytest.raises(RuntimeError, match="scripted user id generation failure"):
        _ = order.user_id
    assert "user_id" not in order.field_cache

    assert order.user_id.startswith("USER")
    assert order.user_id == order.field_cache["user_id"]
    assert calls == 2


def test_order_id_claim_failure_propagates_and_retries_candidate(monkeypatch: pytest.MonkeyPatch) -> None:
    generated = 0
    claims = 0

    def candidate(pattern: str, *, rng: Random) -> str:
        nonlocal generated
        generated += 1
        return f"A{generated:07d}"

    order = Order(OrderGenerator(dataset="US", rng=Random(902)))

    def claim_once(name: str, value: str) -> str:
        nonlocal claims
        claims += 1
        if claims == 1:
            raise RuntimeError("scripted order identifier claim failure")
        return value

    monkeypatch.setattr(StringGenerator, "rnd_str_from_regex", staticmethod(candidate))
    monkeypatch.setattr(order, "_claim_identifier", claim_once)

    with pytest.raises(RuntimeError, match="scripted order identifier claim failure"):
        _ = order.order_id
    assert "order_id" not in order.field_cache

    assert order.order_id == "ORDA0000002"
    assert generated == 2
    assert claims == 2


def test_order_and_user_id_access_order_preserves_seeded_values_and_rng_states() -> None:
    order_first_rng = Random(902)
    order_first_generator = OrderGenerator(dataset="US", rng=order_first_rng)
    order_first = Order(order_first_generator)
    assert _fingerprint(order_first_rng) == "d79864a770071ad644e17182785e0cc62cf4a45cde278e3c39c7c17b732cec56"
    assert order_first.order_id == "ORDJ8M7J6TV"
    assert _fingerprint(order_first_rng) == "7920150bfa93ad5a103a2e7a605196cab3bca519eb9ac6ad3dc2438bd9420303"
    assert order_first.user_id == "USERR6KKT1RV"
    assert _fingerprint(order_first_rng) == "9a6b64784b7dd9be872b8299c91cd4329d7947c162e7e0855c4fe99985f4246e"

    user_first_rng = Random(902)
    user_first_generator = OrderGenerator(dataset="US", rng=user_first_rng)
    user_first = Order(user_first_generator)
    assert _fingerprint(user_first_rng) == "d79864a770071ad644e17182785e0cc62cf4a45cde278e3c39c7c17b732cec56"
    assert user_first.user_id == "USERJ8M7J6TV"
    assert _fingerprint(user_first_rng) == "7920150bfa93ad5a103a2e7a605196cab3bca519eb9ac6ad3dc2438bd9420303"
    assert user_first.order_id == "ORDR6KKT1RV"
    assert _fingerprint(user_first_rng) == "9a6b64784b7dd9be872b8299c91cd4329d7947c162e7e0855c4fe99985f4246e"


def test_order_serialization_keeps_id_fields_first_and_in_order() -> None:
    order = Order(OrderGenerator(dataset="US", rng=Random(902)))

    serialized = order.to_dict()

    assert list(serialized)[:3] == ["order_id", "user_id", "product_list"]
