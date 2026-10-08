from __future__ import annotations

from hashlib import sha256
from random import Random

import pytest

from datamimic_ce.domains.ecommerce.generators.product_generator import ProductGenerator
from datamimic_ce.domains.ecommerce.models.product import Product
from datamimic_ce.domains.shared.literal_generators.primitives.string_generator import StringGenerator


def _rng_fingerprint(rng: Random) -> str:
    return sha256(repr(rng.getstate()).encode()).hexdigest()


def _product(seed: int) -> tuple[Product, ProductGenerator, Random]:
    rng = Random(seed)
    generator = ProductGenerator(dataset="US", rng=rng)
    return Product(generator), generator, rng


def test_sku_first_and_category_first_preserve_seeded_output_and_rng_state() -> None:
    sku_first, _, sku_first_rng = _product(901)
    assert _rng_fingerprint(sku_first_rng) == "07dda516cb25ce3c43fd154276ee68f0bf4c8d2803ce208f657618d1c6e88b8c"
    assert sku_first.sku == "BEA-BEA-674576"
    assert _rng_fingerprint(sku_first_rng) == "0ea94baf59e36b262d931b1a6b3243d99b48df543a113a45e2b409bdf6dbb726"
    assert sku_first.category == "BEAUTY"
    assert _rng_fingerprint(sku_first_rng) == "0ea94baf59e36b262d931b1a6b3243d99b48df543a113a45e2b409bdf6dbb726"

    category_first, _, category_first_rng = _product(901)
    assert _rng_fingerprint(category_first_rng) == "07dda516cb25ce3c43fd154276ee68f0bf4c8d2803ce208f657618d1c6e88b8c"
    assert category_first.category == "SPORTS"
    assert _rng_fingerprint(category_first_rng) == "289492a3f5c99632e421e4023ffe0148ab5b42ba9646794407641269d65df9d0"
    assert category_first.sku == "GOU-SPO-674576"
    assert _rng_fingerprint(category_first_rng) == "0ea94baf59e36b262d931b1a6b3243d99b48df543a113a45e2b409bdf6dbb726"


def test_sku_uses_six_digit_regex_and_preserves_leading_zeroes(monkeypatch: pytest.MonkeyPatch) -> None:
    class DigitRandom(Random):
        def __init__(self) -> None:
            super().__init__(1)
            self.choice_inputs: list[list[str]] = []

        def choice(self, sequence):
            self.choice_inputs.append(sequence)
            return sequence[0]

    rng = DigitRandom()
    product = Product(ProductGenerator(dataset="US", rng=rng))
    product._field_cache.update(brand="Acme", category="beauty")

    assert product.sku == "ACM-BEA-000000"
    assert rng.choice_inputs == [[str(digit) for digit in range(10)]] * 6


def test_sku_is_lazy_cached_and_reads_public_rng_once() -> None:
    class RngObservedGenerator(ProductGenerator):
        rng_reads = 0

        @property
        def rng(self) -> Random:
            self.rng_reads += 1
            return self._rng

    rng = Random(901)
    generator = RngObservedGenerator(dataset="US", rng=rng)
    product = Product(generator)
    product._field_cache.update(brand="Acme", category="beauty")
    generator.rng_reads = 0

    assert "sku" not in product.field_cache
    assert generator.rng_reads == 0
    assert product.sku == "ACM-BEA-419267"
    assert generator.rng_reads == 1
    state_after_sku = rng.getstate()
    assert product.sku == "ACM-BEA-419267"
    assert rng.getstate() == state_after_sku
    assert generator.rng_reads == 1


def test_sku_retries_after_regex_generation_failure_without_caching(monkeypatch: pytest.MonkeyPatch) -> None:
    original = StringGenerator.rnd_str_from_regex
    calls = 0

    def fail_once(pattern: str, *, rng) -> str:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("scripted SKU draw failure")
        return original(pattern, rng=rng)

    monkeypatch.setattr(StringGenerator, "rnd_str_from_regex", staticmethod(fail_once))
    product = Product(ProductGenerator(dataset="US", rng=Random(901)))
    product._field_cache.update(brand="Acme", category="beauty")

    with pytest.raises(RuntimeError, match="scripted SKU draw failure"):
        _ = product.sku
    assert "sku" not in product.field_cache

    assert product.sku == "ACM-BEA-419267"
    assert calls == 2


def test_sku_delegates_after_evaluating_brand_then_category() -> None:
    events: list[object] = []

    class CandidateGenerator(ProductGenerator):
        def generate_sku(self, brand: str, category: str) -> str:
            events.append(("generate_sku", brand, category))
            return "ACM-BEA-000007"

    class EventProduct(Product):
        @property
        def brand(self) -> str:
            events.append("brand")
            return "Acme"

        @property
        def category(self) -> str:
            events.append("category")
            return "beauty"

    product = EventProduct(CandidateGenerator(dataset="US", rng=Random(901)))

    assert product.sku == "ACM-BEA-000007"
    assert events == ["brand", "category", ("generate_sku", "Acme", "beauty")]


def test_name_first_sku_first_and_description_first_preserve_seeded_outputs_and_rng_states() -> None:
    name_first, _, name_first_rng = _product(1401)
    assert _rng_fingerprint(name_first_rng) == "3d67964d2b1b5f7ca641b7bc7c05ff2be7cf8f07e01cc9a1f40d8b55e78116ef"
    assert name_first.name == "Premium BeautyEssentials Coffee"
    assert _rng_fingerprint(name_first_rng) == "e8e674b42f34d32278b140cb5144a782dfc99e2e9cd6cad3bcf834f2b71786ae"
    assert name_first.description == (
        "Premium BeautyEssentials Coffee - Sustainably sourced, No added sugar. "
        "This premium beverages product offers exceptional quality and value. "
        "One of our best-selling products"
    )
    assert _rng_fingerprint(name_first_rng) == "c03ab4a6b633aba71056360601301eb8fbfd9629d283af028c6a7b22aed7a68e"

    sku_first, _, sku_first_rng = _product(1401)
    assert _rng_fingerprint(sku_first_rng) == "3d67964d2b1b5f7ca641b7bc7c05ff2be7cf8f07e01cc9a1f40d8b55e78116ef"
    assert sku_first.sku == "BOO-SPO-276924"
    assert _rng_fingerprint(sku_first_rng) == "363a570111482a77059454aafb3603a7605f2ce106fb92b20c2bf2d051b3f03c"
    assert sku_first.name == "BookWorm Shin Guards"
    assert _rng_fingerprint(sku_first_rng) == "342643b4a8393cdbdb21b4b7706a162a9f553ed1517d4be9105340101757b229"
    assert sku_first.description == (
        "BookWorm Shin Guards - Adjustable fit, Lightweight, High performance. "
        "This premium sports product offers exceptional quality and value. "
        "Designed with customer satisfaction in mind"
    )
    assert _rng_fingerprint(sku_first_rng) == "e7a6b622d93c43f4206abb66221cb6e22e28f685933d1de18a4f237a7da44746"

    description_first, _, description_first_rng = _product(1401)
    assert _rng_fingerprint(description_first_rng) == "3d67964d2b1b5f7ca641b7bc7c05ff2be7cf8f07e01cc9a1f40d8b55e78116ef"
    assert description_first.description == (
        "Premium BeautyEssentials Coffee - Sustainably sourced, No added sugar. "
        "This premium beverages product offers exceptional quality and value. "
        "One of our best-selling products"
    )
    assert _rng_fingerprint(description_first_rng) == "c03ab4a6b633aba71056360601301eb8fbfd9629d283af028c6a7b22aed7a68e"
    state_after_description = description_first_rng.getstate()
    assert description_first.description == (
        "Premium BeautyEssentials Coffee - Sustainably sourced, No added sugar. "
        "This premium beverages product offers exceptional quality and value. "
        "One of our best-selling products"
    )
    assert description_first_rng.getstate() == state_after_description


class _ProductTraceRandom(Random):
    def __init__(self, events: list[object], *, choice_index: int = 0) -> None:
        super().__init__(1)
        self.events = events
        self.choice_index = choice_index

    def choice(self, sequence):
        self.events.append(("choice", tuple(sequence)))
        return sequence[self.choice_index]


class _TracingProductGenerator(ProductGenerator):
    def __init__(self, events: list[object], *, noun: str = "Phone", fail_data_type: str | None = None) -> None:
        self.events = events
        self.noun = noun
        self.fail_data_type = fail_data_type
        self.failures_remaining = 1
        rng = _ProductTraceRandom(events, choice_index=1)
        super().__init__(dataset="US", rng=rng)
        events.clear()

    @property
    def rng(self) -> Random:
        self.events.append("rng")
        return self._rng

    def get_product_data_by_data_type(self, data_type: str) -> str:
        self.events.append(data_type)
        if data_type == self.fail_data_type and self.failures_remaining:
            self.failures_remaining -= 1
            raise OSError("scripted product dataset load failure")
        return {
            "product_categories": "Electronics",
            "product_brands": "Acme",
            "product_adjectives": "Premium",
            "product_nouns_Electronics": self.noun,
        }[data_type]


def test_name_resolves_category_brand_adjective_noun_then_rng_choice_in_pattern_order() -> None:
    events: list[object] = []
    generator = _TracingProductGenerator(events)
    product = Product(generator)
    patterns = (
        "Acme Premium Phone",
        "Premium Phone by Acme",
        "Acme Phone",
        "Premium Acme Phone",
    )

    assert product.name == patterns[1]
    assert events == [
        "product_categories",
        "product_brands",
        "product_adjectives",
        "product_nouns_Electronics",
        "rng",
        ("choice", patterns),
    ]
    event_count = len(events)
    assert product.name == patterns[1]
    assert len(events) == event_count


def test_missing_category_noun_fails_before_rng_access() -> None:
    events: list[object] = []
    product = Product(_TracingProductGenerator(events, noun=""))

    with pytest.raises(ValueError, match="No product nouns for category 'Electronics'"):
        _ = product.name

    assert "name" not in product.field_cache
    assert "rng" not in events
    assert events == ["product_categories", "product_brands", "product_adjectives", "product_nouns_Electronics"]


def test_name_loader_failure_retries_with_category_and_brand_cached() -> None:
    events: list[object] = []
    generator = _TracingProductGenerator(events, fail_data_type="product_adjectives")
    product = Product(generator)

    with pytest.raises(OSError, match="scripted product dataset load failure"):
        _ = product.name
    assert "name" not in product.field_cache
    assert product.field_cache["category"] == "Electronics"
    assert product.field_cache["brand"] == "Acme"
    assert events == ["product_categories", "product_brands", "product_adjectives"]

    assert product.name == "Premium Phone by Acme"
    assert events == [
        "product_categories",
        "product_brands",
        "product_adjectives",
        "product_adjectives",
        "product_nouns_Electronics",
        "rng",
        ("choice", ("Acme Premium Phone", "Premium Phone by Acme", "Acme Phone", "Premium Acme Phone")),
    ]


def test_name_uses_separate_property_caches_for_products_sharing_generator() -> None:
    events: list[object] = []
    generator = _TracingProductGenerator(events)
    first, second = Product(generator), Product(generator)

    assert first.name == "Premium Phone by Acme"
    first_event_count = len(events)
    assert first.name == "Premium Phone by Acme"
    assert len(events) == first_event_count
    assert second.name == "Premium Phone by Acme"
    assert events.count("product_categories") == 2
    assert events.count("product_brands") == 2


def test_name_generation_delegates_to_generator_with_category_then_brand() -> None:
    events: list[object] = []

    class CandidateGenerator(_TracingProductGenerator):
        def generate_name(self, category: str, brand: str) -> str:
            events.append(("generate_name", category, brand))
            return "candidate-name"

    generator = CandidateGenerator(events)
    product = Product(generator)

    assert product.name == "candidate-name"
    assert events == [
        "product_categories",
        "product_brands",
        ("generate_name", "Electronics", "Acme"),
    ]


def test_sku_keeps_its_distinct_brand_then_category_evaluation_order() -> None:
    events: list[object] = []

    class RngObservedGenerator(ProductGenerator):
        @property
        def rng(self) -> Random:
            events.append("rng")
            return self._rng

    class OrderedProduct(Product):
        @property
        def brand(self) -> str:
            events.append("brand")
            return "Acme"

        @property
        def category(self) -> str:
            events.append("category")
            return "beauty"

    rng = _ProductTraceRandom(events)
    product = OrderedProduct(RngObservedGenerator(dataset="US", rng=rng))

    assert product.sku == "ACM-BEA-000000"
    assert events == ["brand", "category", "rng"] + [("choice", tuple(str(digit) for digit in range(10)))] * 6


def test_description_orders_name_category_features_then_benefit_without_rng_accessor() -> None:
    events: list[object] = []

    class DescriptionGenerator(_TracingProductGenerator):
        def get_random_features(self, category: str, min_feature: int = 1, max_feature: int = 1) -> list[str]:
            events.append(("features", category, min_feature, max_feature))
            return ["Fast", "Safe"]

        def get_product_data_by_data_type(self, data_type: str) -> str:
            if data_type == "product_benefits":
                events.append("product_benefits")
                return "Built for daily use"
            return super().get_product_data_by_data_type(data_type)

    generator = DescriptionGenerator(events)
    product = Product(generator)
    expected = (
        "Premium Phone by Acme - Fast, Safe. This premium electronics product offers exceptional quality and value. "
        "Built for daily use"
    )

    assert product.description == expected
    assert events == [
        "product_categories",
        "product_brands",
        "product_adjectives",
        "product_nouns_Electronics",
        "rng",
        ("choice", ("Acme Premium Phone", "Premium Phone by Acme", "Acme Phone", "Premium Acme Phone")),
        ("features", "Electronics", 2, 3),
        "product_benefits",
    ]


def test_feature_failure_happens_before_benefit_selection() -> None:
    events: list[object] = []

    class FeatureFailsGenerator(_TracingProductGenerator):
        def get_random_features(self, category: str, min_feature: int = 1, max_feature: int = 1) -> list[str]:
            events.append(("features", category, min_feature, max_feature))
            raise RuntimeError("scripted feature failure")

        def get_product_data_by_data_type(self, data_type: str) -> str:
            events.append(data_type)
            return super().get_product_data_by_data_type(data_type)

    product = Product(FeatureFailsGenerator(events))

    with pytest.raises(RuntimeError, match="scripted feature failure"):
        _ = product.description

    assert "description" not in product.field_cache
    assert "product_benefits" not in events
    assert events[-1] == ("features", "Electronics", 2, 3)


def test_benefit_failure_keeps_name_and_category_cached_then_resamples_features() -> None:
    events: list[object] = []

    class BenefitFailsOnceGenerator(_TracingProductGenerator):
        feature_calls = 0
        benefit_calls = 0

        def get_random_features(self, category: str, min_feature: int = 1, max_feature: int = 1) -> list[str]:
            self.feature_calls += 1
            events.append(("features", category, min_feature, max_feature))
            return [f"feature-{self.feature_calls}"]

        def get_product_data_by_data_type(self, data_type: str) -> str:
            if data_type == "product_benefits":
                self.benefit_calls += 1
                events.append("product_benefits")
                if self.benefit_calls == 1:
                    raise OSError("scripted benefit loader failure")
                return "Good value"
            return super().get_product_data_by_data_type(data_type)

    generator = BenefitFailsOnceGenerator(events)
    product = Product(generator)

    with pytest.raises(OSError, match="scripted benefit loader failure"):
        _ = product.description
    assert "description" not in product.field_cache
    assert product.field_cache["name"] == "Premium Phone by Acme"
    assert product.field_cache["category"] == "Electronics"

    assert product.description == (
        "Premium Phone by Acme - feature-2. This premium electronics product offers exceptional quality and value. "
        "Good value"
    )
    assert generator.feature_calls == 2
    assert generator.benefit_calls == 2
    cached_description = product.description
    assert product.description is cached_description
    assert generator.feature_calls == 2
    assert generator.benefit_calls == 2


def test_descriptions_are_cached_per_product_when_generator_is_shared() -> None:
    class CountingGenerator(ProductGenerator):
        feature_calls = 0
        benefit_calls = 0

        def get_random_features(self, category: str, min_feature: int = 1, max_feature: int = 1) -> list[str]:
            self.feature_calls += 1
            return [f"feature-{self.feature_calls}"]

        def get_product_data_by_data_type(self, data_type: str) -> str:
            if data_type == "product_benefits":
                self.benefit_calls += 1
                return f"benefit-{self.benefit_calls}"
            return super().get_product_data_by_data_type(data_type)

    generator = CountingGenerator(dataset="US", rng=Random(1401))
    first, second = Product(generator), Product(generator)
    for product in (first, second):
        product._field_cache.update(name="Example", category="Tools")

    assert first.description == (
        "Example - feature-1. This premium tools product offers exceptional quality and value. benefit-1"
    )
    first_description = first.description
    assert generator.feature_calls == 1
    assert generator.benefit_calls == 1
    assert second.description == (
        "Example - feature-2. This premium tools product offers exceptional quality and value. benefit-2"
    )
    second_description = second.description
    assert second_description is not first_description
    assert generator.feature_calls == 2
    assert generator.benefit_calls == 2
    assert second.description is second_description
    assert generator.feature_calls == 2
    assert generator.benefit_calls == 2


def test_random_features_keep_unknown_category_fallback_and_empty_category_behavior(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(ProductGenerator, "_load_product_json", staticmethod(lambda _file_name: {"Empty": []}))

    class NoPublicRngGenerator(ProductGenerator):
        @property
        def rng(self) -> Random:
            raise AssertionError("feature selection must use its existing internal RNG")

    generator = NoPublicRngGenerator(dataset="US", rng=Random(1401))

    unknown = generator.get_random_features("Unknown", min_feature=2, max_feature=3)
    empty = generator.get_random_features("Empty", min_feature=2, max_feature=3)

    assert unknown
    assert len(unknown) in {2, 3}
    assert set(unknown) <= {"High quality", "Versatile", "Durable"}
    assert empty == []


def test_description_delegates_to_generator() -> None:
    class CandidateGenerator(ProductGenerator):
        calls: list[tuple[str, str]] = []

        def generate_description(self, name: str, category: str) -> str:
            self.calls.append((name, category))
            return "candidate-description"

    generator = CandidateGenerator(dataset="US", rng=Random(1401))
    product = Product(generator)
    product._field_cache.update(name="Example", category="Tools")

    assert product.description == "candidate-description"
    assert generator.calls == [("Example", "Tools")]
