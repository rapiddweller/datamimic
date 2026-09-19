"""Wall-clock SPOT for CE.

``now_utc_naive()`` is the only sanctioned wall-clock read in CE
production code. Raw ``datetime.datetime.now(...)`` / ``utcnow(...)`` are
forbidden inside ``datamimic_ce/**``; the clock-drift architecture gate
AST-walks the tree to enforce this.

``resolve_clock`` returns either the fixed deterministic anchor or live
UTC, anchored once at construction time.
"""

from __future__ import annotations

from datetime import datetime, timezone
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
    return datetime.now(timezone.utc).replace(tzinfo=None)


def from_epoch_utc(seconds: float) -> datetime:
    """Epoch seconds -> naive UTC datetime, independent of the host timezone."""
    return datetime.fromtimestamp(seconds, timezone.utc).replace(tzinfo=None)


def to_epoch_utc(value: datetime) -> float:
    """Datetime -> epoch seconds; naive values are UTC (CE convention), not host-local."""
    return (value if value.tzinfo else value.replace(tzinfo=timezone.utc)).timestamp()


def resolve_clock(*, deterministic: bool) -> datetime:
    """Return the deterministic anchor if ``deterministic`` else live UTC."""
    return DETERMINISTIC_ANCHOR if deterministic else now_utc_naive()
