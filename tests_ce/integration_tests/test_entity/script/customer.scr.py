"""Helper functions for deterministic customer descriptors."""

from __future__ import annotations

import datetime as _dt
import hashlib
from random import Random
from typing import Iterable

from datamimic_ce.domains.common.models.person import Person


def _derive_seed(person: Person, cohort: str) -> int:
    """Create a stable seed based on person attributes and cohort label."""

    material = f"{cohort}|{person.email}|{person.birthdate}|{person.gender}".encode("utf-8")
    digest = hashlib.blake2b(material, digest_size=8).digest()
    return int.from_bytes(digest, "big", signed=False)


def select_payment_method(person: Person, options: Iterable[str], cohort: str) -> str:
    """Pick a payment method deterministically for the given person."""

    options_tuple = tuple(options)
    if not options_tuple:
        raise ValueError("select_payment_method requires at least one option")

    rng = Random(_derive_seed(person, cohort))
    # Use per-person RNG so locale-specific cohorts stay reproducible across runs.
    return options_tuple[rng.randrange(len(options_tuple))]


def stable_customer_id(person: Person, cohort: str) -> str:
    """Compute a deterministic customer identifier."""

    material = f"{cohort}|{person.email}|{person.name}|{person.birthdate}".encode("utf-8")
    digest = hashlib.blake2b(material, digest_size=10).hexdigest()
    return f"cust-{digest[:20]}"


def stable_customer_since(person: Person, cohort: str) -> str:
    """Return a deterministic ISO-8601 date for `customer_since`."""

    seed = _derive_seed(person, f"{cohort}|since")
    rng = Random(seed)
    year = 2010 + rng.randrange(0, 15)
    month = 1 + rng.randrange(0, 12)
    day = 1 + rng.randrange(0, 28)
    # Anchor relative tenure to calendar dates so repeated runs avoid time-dependent drift.
    return _dt.date(year, month, day).isoformat()
