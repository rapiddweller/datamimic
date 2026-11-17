"""Domain generators draw weighted values by their declared weights; consecutive repeats are allowed (#635)."""

from collections import Counter
from collections.abc import Callable
from pathlib import Path
from random import Random

from datamimic_ce.domains.domain_core.datasets.path import dataset_path
from datamimic_ce.domains.finance.generators.bank_account_generator import BankAccountGenerator
from datamimic_ce.domains.insurance.generators.insurance_policy_generator import InsurancePolicyGenerator
from datamimic_ce.domains.shared.datasets.loader import load_weighted_values_try_dataset, pick_one_weighted_no_repeat

DRAWS = 6000
TOLERANCE = 0.03
HERE = Path(__file__)


def _declared(values: list[str], weights: list[float]) -> dict[str, float]:
    total = sum(weights)
    shares: dict[str, float] = {}
    for value, weight in zip(values, weights, strict=True):
        shares[value] = shares.get(value, 0.0) + weight / total
    return shares


def _assert_frequencies(draw: Callable[[], str], declared: dict[str, float]) -> list[str]:
    drawn = [draw() for _ in range(DRAWS)]
    counts = Counter(drawn)
    assert set(counts) <= set(declared)
    for value, share in declared.items():
        assert abs(counts[value] / DRAWS - share) < TOLERANCE, (value, counts[value] / DRAWS, share)
    return drawn


def _policy_statuses() -> tuple[InsurancePolicyGenerator, dict[str, float]]:
    values, weights = load_weighted_values_try_dataset("insurance", "policy", "statuses.csv", dataset="US", start=HERE)
    return InsurancePolicyGenerator(dataset="US", rng=Random(1)), _declared(values, weights)


def test_policy_status_frequencies_match_declared_weights():
    generator, declared = _policy_statuses()
    drawn = _assert_frequencies(lambda: generator.pick_status(start_path=HERE), declared)
    assert any(a == b for a, b in zip(drawn, drawn[1:], strict=False))


def test_currency_frequencies_match_declared_weights():
    generator = BankAccountGenerator(dataset="US", rng=Random(2))
    path = dataset_path("ecommerce", "currencies_US.csv", start=HERE)
    header, *rows = [line.split(",") for line in path.read_text(encoding="utf-8").splitlines()]
    code, weight = header.index("code"), header.index("weight")
    declared = _declared([r[code] for r in rows], [float(r[weight]) for r in rows])
    _assert_frequencies(generator.get_currency, declared)


def test_account_type_frequencies_match_declared_weights():
    generator = BankAccountGenerator(dataset="US", rng=Random(3))
    path = dataset_path("finance", "account_types_US.csv", start=HERE)
    _, *rows = [line.split(",") for line in path.read_text(encoding="utf-8").splitlines()]
    declared = _declared([r[0] for r in rows], [float(r[1]) for r in rows])
    _assert_frequencies(generator.get_bank_account_types, declared)


def test_same_seed_reproduces_weighted_values():
    def statuses(seed: int) -> list[str]:
        generator = InsurancePolicyGenerator(dataset="US", rng=Random(seed))
        return [generator.pick_status(start_path=HERE) for _ in range(50)]

    assert statuses(4) == statuses(4)
    assert statuses(4) != statuses(5)


def test_no_repeat_picking_fails_the_frequency_check():
    """Negative control: the old no-repeat behaviour distorts the declared shares beyond the tolerance."""
    _, declared = _policy_statuses()
    values = list(declared)
    weights = list(declared.values())
    rng = Random(1)
    last = None
    drawn = []
    for _ in range(DRAWS):
        last = pick_one_weighted_no_repeat(rng, values, weights, last=last)
        drawn.append(last)
    top = max(declared, key=lambda v: declared[v])
    assert abs(drawn.count(top) / DRAWS - declared[top]) > TOLERANCE
