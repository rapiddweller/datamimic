# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Tests for Faker-backed generator determinism.

Each parametrised case verifies:
  1. Same seed → byte-identical output across 10 independent instantiations.
  2. Different seeds → output diverges (at least one value differs in 10 draws).
  3. No seed/rng → smoke test; output is a non-empty string.
"""

import random
from collections.abc import Callable
from typing import Any

import pytest

from datamimic_ce.domains.common.literal_generators.cnpj_generator import CNPJGenerator
from datamimic_ce.domains.common.literal_generators.cpf_generator import CPFGenerator
from datamimic_ce.domains.common.literal_generators.data_faker_generator import DataFakerGenerator
from datamimic_ce.domains.common.literal_generators.ean_generator import EANGenerator
from datamimic_ce.domains.common.literal_generators.ssn_generator import SSNGenerator
from datamimic_ce.domains.common.literal_generators.url_generator import UrlGenerator

# ---------------------------------------------------------------------------
# Fixtures — factory callables keyed by a human-readable name.
# Each factory accepts (rng) and returns a generator with a .generate() method.
# Adding a new Faker-backed generator later is one entry here.
# ---------------------------------------------------------------------------

GENERATOR_FACTORIES: list[tuple[str, Callable[[random.Random | None], Any]]] = [
    (
        "DataFakerGenerator(name)",
        lambda rng: DataFakerGenerator(method="name", rng=rng),
    ),
    (
        "SSNGenerator",
        lambda rng: SSNGenerator(rng=rng),
    ),
    (
        "CPFGenerator",
        lambda rng: CPFGenerator(rng=rng),
    ),
    (
        "CNPJGenerator",
        lambda rng: CNPJGenerator(rng=rng),
    ),
    (
        "UrlGenerator",
        lambda rng: UrlGenerator(rng=rng),
    ),
    (
        "EANGenerator",
        lambda rng: EANGenerator(rng=rng),
    ),
]

FACTORY_IDS = [name for name, _ in GENERATOR_FACTORIES]

_SEED = 42
_RUNS = 10


def _collect(factory: Callable[[random.Random | None], Any], seed: int, n: int = _RUNS) -> list[Any]:
    """Create a fresh rng seeded to `seed`, build a generator, collect n values."""
    rng = random.Random(seed)
    gen = factory(rng)
    return [gen.generate() for _ in range(n)]


# ---------------------------------------------------------------------------
# Test 1: Same seed → byte-identical output
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name,factory", GENERATOR_FACTORIES, ids=FACTORY_IDS)
def test_same_seed_produces_identical_output(name: str, factory: Callable) -> None:
    """Two independent runs with the same seed must produce the same sequence."""
    run_a = _collect(factory, _SEED)
    run_b = _collect(factory, _SEED)
    assert run_a == run_b, (
        f"{name}: expected identical output for seed={_SEED}, got divergence.\n"
        f"run_a={run_a}\nrun_b={run_b}"
    )


# ---------------------------------------------------------------------------
# Test 2: Different seeds → output diverges
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name,factory", GENERATOR_FACTORIES, ids=FACTORY_IDS)
def test_different_seeds_produce_different_output(name: str, factory: Callable) -> None:
    """Two runs with different seeds must not produce the exact same sequence."""
    run_seed1 = _collect(factory, seed=1)
    run_seed2 = _collect(factory, seed=999999)
    assert run_seed1 != run_seed2, (
        f"{name}: expected different output for different seeds, but sequences are identical."
    )


# ---------------------------------------------------------------------------
# Test 3: No seed/rng → smoke test (non-empty string, no crash)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name,factory", GENERATOR_FACTORIES, ids=FACTORY_IDS)
def test_no_seed_smoke(name: str, factory: Callable) -> None:
    """Without a seed the generator must still produce a non-empty value."""
    gen = factory(None)
    value = gen.generate()
    assert value is not None, f"{name}: generate() returned None without seed"
    assert str(value).strip() != "", f"{name}: generate() returned empty string without seed"
