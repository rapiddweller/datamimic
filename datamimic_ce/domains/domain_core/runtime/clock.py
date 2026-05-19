"""Wall-clock SPOT for CE.

``now_utc_naive`` is the only sanctioned wall-clock read in CE production
code. Raw ``datetime.datetime.now(...)`` and ``datetime.datetime.utcnow(...)``
are forbidden inside ``datamimic_ce/**`` — the clock-drift architecture
gate AST-walks the production tree to enforce this.

The contract mirrors EE's ADR-030. Two modes:

* **Live wall-clock** — ``now_utc_naive()`` returns the current UTC time
  as a naive ``datetime``. Use this only when the generator's policy is
  explicitly non-deterministic.

* **Deterministic anchor** — :data:`DETERMINISTIC_ANCHOR` is the fixed
  point in time used whenever a generator runs in seeded mode and needs
  "now". A static anchor keeps the output reproducible across runs and
  machines.

Use :func:`resolve_clock` to get one or the other based on the
``deterministic`` policy, mirroring how :func:`resolve_rng` works.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Final

DETERMINISTIC_ANCHOR: Final[datetime] = datetime(2025, 1, 1, 12, 0, 0)
"""Fixed "now" used in seeded mode. Mirrors EE's ADR-030 anchor."""


def now_utc_naive() -> datetime:
    """Return current UTC time as a naive :class:`datetime`.

    This is the single allowed wall-clock read in CE production code.
    All other ``datetime.now()``/``datetime.utcnow()`` callsites in
    ``datamimic_ce/**`` are flagged by the clock-drift architecture gate.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


def resolve_clock(*, deterministic: bool = False) -> datetime:
    """Return either the deterministic anchor or current UTC.

    Generators that need a "now"-derived value (e.g. founding year,
    transaction date, age computation) should call this — never raw
    ``datetime.now()`` — so that switching from non-deterministic to
    seeded mode is a single policy flag, not a code change in every
    generator.
    """
    return DETERMINISTIC_ANCHOR if deterministic else now_utc_naive()
