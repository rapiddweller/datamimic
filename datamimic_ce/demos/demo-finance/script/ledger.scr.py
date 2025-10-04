from __future__ import annotations

from random import Random

# Demo helper for composing account-centric ledgers
#  Showcase nestedKey with programmatic generation and deterministic RNG
from typing import Any

from datamimic_ce.domains.finance.generators.transaction_generator import TransactionGenerator
from datamimic_ce.domains.finance.models.transaction import Transaction


def generate_transactions_for_account(account, n: int = 5, seed: int | None = None) -> list[dict[str, Any]]:
    """Generate n transactions tied to the given BankAccount model.

    The generator uses an optional seed for reproducibility and attaches the
    provided `account` so currency and fields align.
    """
    rng = Random(seed) if seed is not None else None
    gen = TransactionGenerator(dataset=account._bank_account_generator.dataset, rng=rng)
    rows: list[dict[str, Any]] = []
    for _ in range(max(0, n)):
        tx = Transaction(gen, bank_account=account)
        rows.append(tx.to_dict())
    return rows
