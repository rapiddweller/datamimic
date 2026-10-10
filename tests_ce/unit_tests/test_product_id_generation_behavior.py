from __future__ import annotations

from hashlib import sha256
from random import Random

import pytest

from datamimic_ce.domains.ecommerce.generators.product_generator import ProductGenerator
from datamimic_ce.domains.ecommerce.models.product import Product
from datamimic_ce.domains.ecommerce.services.product_service import ProductService
from datamimic_ce.domains.shared.literal_generators.identity.keys import prefixed_id_generator
from datamimic_ce.domains.shared.literal_generators.primitives.string_generator import StringGenerator


def _fingerprint(rng: Random) -> str:
    return sha256(repr(rng.getstate()).encode()).hexdigest()


class _ObservedProductGenerator(ProductGenerator):
    def __init__(self, rng: Random) -> None:
        self.rng_reads = 0
        super().__init__(dataset="US", rng=rng)

    @property
    def rng(self) -> Random:
        self.rng_reads += 1
        return self._rng


def test_product_construction_is_lazy_and_id_uses_exact_prefixed_generator_arguments(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, str, str, Random]] = []

    class RecordingPrefixedIdGenerator:
        def __init__(self, prefix: str, pattern: str, separator: str, rng: Random) -> None:
            calls.append((prefix, pattern, separator, rng))

        def generate(self) -> str:
            return "PROD0000A001"

    monkeypatch.setattr(prefixed_id_generator, "PrefixedIdGenerator", RecordingPrefixedIdGenerator)
    rng = Random(901)
    generator = _ObservedProductGenerator(rng)
    product = Product(generator)
    initial_state = rng.getstate()

    assert product.field_cache == {}
    assert generator.rng_reads == 0
    assert rng.getstate() == initial_state
    assert product.product_id == "PROD0000A001"
    assert calls == [("PROD", "[A-Z0-9]{8}", "", rng)]
    assert generator.rng_reads == 1
    assert product.product_id == "PROD0000A001"
    assert generator.rng_reads == 1
    assert len(calls) == 1


def test_product_id_candidate_delegates_to_generator() -> None:
    class CandidateGenerator(ProductGenerator):
        def generate_product_id_candidate(self) -> str:
            return "PRODTEST1234"

    product = Product(CandidateGenerator(dataset="US", rng=Random(901)))

    assert product.product_id == "PRODTEST1234"


def test_shared_generator_products_cache_ids_independently_and_allow_unbound_duplicates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def fixed_body(pattern: str, *, rng: Random) -> str:
        nonlocal calls
        calls += 1
        assert pattern == "[A-Z0-9]{8}"
        return "AAAAAAAA"

    monkeypatch.setattr(StringGenerator, "rnd_str_from_regex", staticmethod(fixed_body))
    generator = _ObservedProductGenerator(Random(19))
    first = Product(generator)
    second = Product(generator)

    assert first.product_id == second.product_id == "PRODAAAAAAAA"
    assert first.product_id == "PRODAAAAAAAA"
    assert second.product_id == "PRODAAAAAAAA"
    assert calls == 2
    assert generator.rng_reads == 2


def test_bound_product_id_collision_is_allocated_without_candidate_redraw(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0

    def repeated_body(pattern: str, *, rng: Random) -> str:
        nonlocal calls
        calls += 1
        assert pattern == "[A-Z0-9]{8}"
        return "00000000"

    monkeypatch.setattr(StringGenerator, "rnd_str_from_regex", staticmethod(repeated_body))
    products = ProductService(rng=Random(19)).generate_batch(2)

    assert [product.product_id for product in products] == ["PROD00000000", "PROD00000001"]
    assert calls == 2


def test_product_id_generation_failure_is_uncached_and_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    original = StringGenerator.rnd_str_from_regex
    calls = 0

    def fail_once(pattern: str, *, rng: Random) -> str:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("scripted product id generation failure")
        return original(pattern, rng=rng)

    monkeypatch.setattr(StringGenerator, "rnd_str_from_regex", staticmethod(fail_once))
    product = Product(ProductGenerator(dataset="US", rng=Random(901)))

    with pytest.raises(RuntimeError, match="scripted product id generation failure"):
        _ = product.product_id
    assert "product_id" not in product.field_cache

    assert product.product_id.startswith("PROD")
    assert calls == 2


def test_product_id_claim_failure_propagates_and_retries_candidate(monkeypatch: pytest.MonkeyPatch) -> None:
    generated = 0
    claims = 0

    def candidate(pattern: str, *, rng: Random) -> str:
        nonlocal generated
        generated += 1
        return f"A{generated:07d}"

    product = Product(ProductGenerator(dataset="US", rng=Random(901)))

    def claim_once(name: str, value: str) -> str:
        nonlocal claims
        claims += 1
        if claims == 1:
            raise RuntimeError("scripted identifier claim failure")
        return value

    monkeypatch.setattr(StringGenerator, "rnd_str_from_regex", staticmethod(candidate))
    monkeypatch.setattr(product, "_claim_identifier", claim_once)

    with pytest.raises(RuntimeError, match="scripted identifier claim failure"):
        _ = product.product_id
    assert "product_id" not in product.field_cache

    assert product.product_id == "PRODA0000002"
    assert generated == 2
    assert claims == 2


def test_product_id_name_and_sku_access_order_preserves_seeded_values_and_rng_states() -> None:
    id_first_rng = Random(901)
    id_first_generator = ProductGenerator(dataset="US", rng=id_first_rng)
    id_first = Product(id_first_generator)
    assert _fingerprint(id_first_rng) == "07dda516cb25ce3c43fd154276ee68f0bf4c8d2803ce208f657618d1c6e88b8c"
    assert id_first.product_id == "PRODSHJY5RU5"
    assert _fingerprint(id_first_rng) == "ae58437c994372dbba597f3ee546872255ceffca230bbe2bbdb1c33c0a0f181d"
    assert id_first.name == "BeautyEssentials Digital Bandages"
    assert _fingerprint(id_first_rng) == "8109323b8c25a6d9c82e357d343f2f7a354a977340152cdfd61c5c27e32b6693"
    assert id_first.sku == "BEA-HEA-461591"
    assert _fingerprint(id_first_rng) == "52b34e911c65b923ff5b203e7f07ae422718a23c8785748055bb3cab606c08da"

    name_first_rng = Random(901)
    name_first = Product(ProductGenerator(dataset="US", rng=name_first_rng))
    assert name_first.name == "Organic GourmetDelight Golf Clubs"
    assert _fingerprint(name_first_rng) == "0a580e63810c08c8580c2a7bbe9a10c84c83398faa7cd0a7b097afdffe3ee50e"
    assert name_first.product_id == "PRODU5Y03E6H"
    assert _fingerprint(name_first_rng) == "c2c742d234c7c77057cd80228e9fd85ddd8e46249f66bc5aa4964c5b904226e7"

    sku_first_rng = Random(901)
    sku_first = Product(ProductGenerator(dataset="US", rng=sku_first_rng))
    assert sku_first.sku == "BEA-BEA-674576"
    assert _fingerprint(sku_first_rng) == "0ea94baf59e36b262d931b1a6b3243d99b48df543a113a45e2b409bdf6dbb726"
    assert sku_first.product_id == "PROD3E6HTYGW"
    assert _fingerprint(sku_first_rng) == "8d2fcb3d04113e4821329957df329f773b4193249842feedeb1cca8cbb782949"
