from datetime import datetime, timezone
from hashlib import sha256
from random import Random

import pytest

from datamimic_ce.domains.domain_core.base_entity import IdentifierRegistry
from datamimic_ce.domains.finance.generators.transaction_generator import TransactionGenerator
from datamimic_ce.domains.finance.models.transaction import Transaction
from datamimic_ce.domains.finance.services.transaction_service import TRANSACTION_SCHEMA
from datamimic_ce.domains.shared.literal_generators.primitives.string_generator import StringGenerator

_REFERENCE_NOW = datetime(2026, 9, 29, 10, 30, tzinfo=timezone.utc)


def _transaction(seed: int) -> tuple[Transaction, TransactionGenerator, Random]:
    rng = Random(seed)
    generator = TransactionGenerator(dataset="US", rng=rng, reference_now=_REFERENCE_NOW)
    return Transaction(generator), generator, rng


def _rng_fingerprint(rng: Random) -> str:
    return sha256(repr(rng.getstate()).encode()).hexdigest()


def test_is_international_is_lazy_cached_and_preserves_seeded_rng_state() -> None:
    transaction, _, rng = _transaction(731)

    # Construction must not draw the lazy international flag.
    assert _rng_fingerprint(rng) == "852708e796dff62755e070788f140e9efe0768a57657d1d420dd73c2c7ccd82d"

    assert transaction.is_international is False
    state_after_read = rng.getstate()
    assert _rng_fingerprint(rng) == "bfc40c6d008f8ac78f5fda206f51eb905670aba78246b5f0067c6fe7dd894e11"

    assert transaction.is_international is False
    assert rng.getstate() == state_after_read


def test_transactions_sharing_generator_keep_independent_lazy_property_caches() -> None:
    rng = Random(0)
    generator = TransactionGenerator(dataset="US", rng=rng, reference_now=_REFERENCE_NOW)
    first = Transaction(generator)
    second = Transaction(generator)

    assert first.is_international is True
    state_after_first = rng.getstate()
    assert _rng_fingerprint(rng) == "24b72c99314b2a685122d8837b77e5b6961832ebef7485681a0f5daca60ad6fc"

    assert second.is_international is False
    state_after_second = rng.getstate()
    assert _rng_fingerprint(rng) == "5a7a6c1575438c3461266392bebb240e0be05776dd64a24c7e7c7486d56e369c"

    assert first.is_international is True
    assert second.is_international is False
    assert rng.getstate() == state_after_second
    assert state_after_first != state_after_second


def test_transaction_id_is_lazy_cached_and_uses_exact_public_rng_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    class RngObservedGenerator(TransactionGenerator):
        rng_reads = 0

        @property
        def rng(self) -> Random:
            self.rng_reads += 1
            return self._rng

    calls: list[tuple[str, Random]] = []

    def candidate(pattern: str, *, rng: Random) -> str:
        calls.append((pattern, rng))
        return "A" * 16

    monkeypatch.setattr(StringGenerator, "rnd_str_from_regex", staticmethod(candidate))
    generator = RngObservedGenerator(dataset="US", rng=Random(17), reference_now=_REFERENCE_NOW)
    transaction = Transaction(generator)
    calls.clear()  # Transaction construction also creates a reference number.
    generator.rng_reads = 0

    assert calls == []
    assert generator.rng_reads == 0
    assert transaction.transaction_id == "A" * 16
    assert calls == [("[A-Z0-9]{16}", generator._rng)]
    assert generator.rng_reads == 1
    assert transaction.transaction_id == "A" * 16
    assert len(calls) == 1
    assert generator.rng_reads == 1


def test_transaction_id_collision_uses_registry_alternative_without_redrawing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def duplicate_candidate(_pattern: str, *, rng: Random) -> str:
        nonlocal calls
        calls += 1
        return "A" * 16

    monkeypatch.setattr(StringGenerator, "rnd_str_from_regex", staticmethod(duplicate_candidate))
    generator = TransactionGenerator(dataset="US", rng=Random(17), reference_now=_REFERENCE_NOW)
    registry = IdentifierRegistry()
    first, second = Transaction(generator), Transaction(generator)
    calls = 0  # Construction creates each transaction's reference number.
    for transaction in (first, second):
        transaction._bind_identifier_registry(registry, "Transaction", TRANSACTION_SCHEMA.fields, {})

    assert first.transaction_id == "A" * 16
    assert second.transaction_id == "A" * 15 + "B"
    assert calls == 2


def test_transaction_id_and_international_access_order_preserves_seeded_outputs_and_rng_state() -> None:
    id_first, _, id_first_rng = _transaction(731)
    assert _rng_fingerprint(id_first_rng) == "852708e796dff62755e070788f140e9efe0768a57657d1d420dd73c2c7ccd82d"
    assert id_first.transaction_id == "U3QDEWXGNO6TDUUJ"
    assert _rng_fingerprint(id_first_rng) == "890791f5ef085daedcf03e0efb3fa9638cbe055829b09426691b647abec8d389"
    assert id_first.is_international is False
    assert _rng_fingerprint(id_first_rng) == "75fbb05adfbc1174fc7a7c0bd8e51e76fbae9c6fcd5b8591fc6a20203412c8aa"

    international_first, _, international_first_rng = _transaction(731)
    assert _rng_fingerprint(international_first_rng) == (
        "852708e796dff62755e070788f140e9efe0768a57657d1d420dd73c2c7ccd82d"
    )
    assert international_first.is_international is False
    assert _rng_fingerprint(international_first_rng) == (
        "bfc40c6d008f8ac78f5fda206f51eb905670aba78246b5f0067c6fe7dd894e11"
    )
    assert international_first.transaction_id == "3QDEWXGNO6TDUUJU"
    assert _rng_fingerprint(international_first_rng) == (
        "85262b4771ba6566deceffeeb64755aa869f425f92da9ad81e257e7b3c22a75e"
    )


def test_transaction_id_delegates_candidate_creation_to_generator() -> None:
    class CandidateGenerator(TransactionGenerator):
        calls = 0

        def generate_transaction_id_candidate(self) -> str:
            self.calls += 1
            return "Z" * 16

    generator = CandidateGenerator(dataset="US", rng=Random(17), reference_now=_REFERENCE_NOW)
    transaction = Transaction(generator)

    assert transaction.transaction_id == "Z" * 16
    assert generator.calls == 1
