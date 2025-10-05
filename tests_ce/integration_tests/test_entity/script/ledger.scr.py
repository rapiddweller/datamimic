"""Deterministic ledger helpers for bank account descriptors."""

from __future__ import annotations

import datetime as _dt
import hashlib
from dataclasses import dataclass
from random import Random
from typing import Iterable

from datamimic_ce.domains.finance.models.bank_account import BankAccount


@dataclass(frozen=True)
class _TransactionProfile:
    """Descriptor-friendly shape for a ledger entry."""

    category: str
    merchant: str
    description: str


# Keep category tables small and explicit so seeded RNG picks from a stable universe.
_CREDIT_PROFILES: tuple[_TransactionProfile, ...] = (
    _TransactionProfile("PAYROLL", "Acme Corp", "Monthly salary payment"),
    _TransactionProfile("REFUND", "Marketplace", "Refund for returned goods"),
    _TransactionProfile("INVESTMENT", "Dividend", "Quarterly dividend payout"),
)

_DEBIT_PROFILES: tuple[_TransactionProfile, ...] = (
    _TransactionProfile("GROCERIES", "Fresh Market", "Grocery purchase"),
    _TransactionProfile("UTILITIES", "City Power", "Electricity bill"),
    _TransactionProfile("RENT", "Downtown Properties", "Monthly rent"),
    _TransactionProfile("TRANSPORT", "Metro Transit", "Transit pass reload"),
    _TransactionProfile("DINING", "Cafe Berlin", "Restaurant visit"),
)


def _account_snapshot(account: BankAccount) -> dict[str, str]:
    """Create a deterministic, serialisable snapshot of account details."""

    return {
        "account_number": account.account_number,
        "iban": account.iban,
        "currency": account.currency,
        "bank_code": account.bank_code,
        "bank_name": account.bank_name,
        "bic": account.bic,
    }


def _derive_seed(account: BankAccount, year: int, override_seed: int | None) -> int:
    """Pick a per-account seed that replays deterministically across runs."""

    if override_seed is not None:
        # Allow descriptors to override RNG when cross-ledger coordination is required.
        return override_seed

    material = f"{account.account_number}|{account.iban}|{account.currency}|{year}".encode("utf-8")
    digest = hashlib.blake2b(material, digest_size=8).digest()
    return int.from_bytes(digest, "big", signed=False)


def _tx_id(account_number: str, sequence: int, occurred_at: _dt.datetime, amount: float) -> str:
    """Create a stable identifier for each transaction."""

    material = f"{account_number}|{sequence}|{occurred_at.isoformat()}|{amount:.2f}".encode("utf-8")
    return hashlib.blake2b(material, digest_size=16).hexdigest()


def _scheduled_dates(rng: Random, year: int, count: int) -> Iterable[_dt.datetime]:
    """Generate deterministic transaction timestamps within the target year."""

    start = _dt.datetime(year, 1, 1)
    for _ in range(count):
        day_offset = rng.randrange(0, 365)
        time_offset_seconds = rng.randrange(0, 24 * 3600)
        yield start + _dt.timedelta(days=day_offset, seconds=time_offset_seconds)


def generate_transactions_for_account(
    account: BankAccount,
    count: int,
    year: int,
    *,
    seed: int | None = None,
) -> list[dict[str, object]]:
    """Create deterministic ledger entries for a bank account."""

    rng = Random(_derive_seed(account, year, seed))

    transactions: list[dict[str, object]] = []
    account_details = _account_snapshot(account)

    for idx, occurred_at in enumerate(_scheduled_dates(rng, year, count), start=1):
        is_credit = rng.random() < 0.4
        profile_pool = _CREDIT_PROFILES if is_credit else _DEBIT_PROFILES
        profile = profile_pool[rng.randrange(len(profile_pool))]

        # Tie the amount to RNG so seeded runs emit reproducible signed values.
        magnitude = round(rng.uniform(25.0, 2500.0), 2)
        amount = magnitude if is_credit else -magnitude

        transactions.append(
            {
                "id": _tx_id(account.account_number, idx, occurred_at, amount),
                "sequence": idx,
                "direction": "CREDIT" if is_credit else "DEBIT",
                "category": profile.category,
                "merchant": profile.merchant,
                "description": profile.description,
                "amount": amount,
                "currency": account.currency,
                "occurred_at": occurred_at.isoformat(),
                "account": account_details,
            }
        )

    return transactions
