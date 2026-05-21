"""Wall-clock SPOT for CE.

``now_utc_naive()`` is the only sanctioned wall-clock read in CE
production code. Raw ``datetime.datetime.now(...)`` / ``utcnow(...)`` are
forbidden inside ``datamimic_ce/**``; the clock-drift architecture gate
AST-walks the tree to enforce this.

``resolve_clock`` returns either the fixed deterministic anchor or live
UTC, anchored once at construction time.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Final

DETERMINISTIC_ANCHOR: Final[datetime] = datetime(2025, 1, 1, 12, 0, 0)
"""The fixed "now" used in seeded mode.

The exact value is arbitrary — only its stability matters. It is chosen as a
clean, recent, timezone-neutral instant (midday on a year boundary) so that
"now"-derived fields (age, founding year, expiry dates) compute to realistic
values. Changing it would change every seeded run's date-derived output, so
treat it as a frozen constant. Internal — read via resolve_clock()."""


def now_utc_naive() -> datetime:
    """The single allowed wall-clock read in CE production code."""
    return datetime.now(UTC).replace(tzinfo=None)


def resolve_clock(*, deterministic: bool) -> datetime:
    """Return the deterministic anchor if ``deterministic`` else live UTC."""
    return DETERMINISTIC_ANCHOR if deterministic else now_utc_naive()
