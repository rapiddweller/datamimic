"""
DateTimeGenerator with optional weighted sampling by hour/minute/second and month.

Key improvements over the previous implementation:
- Deterministic RNG with optional seed.
- Month-weighted sampling across an arbitrary date range.
- Boundary-safe time sampling when the chosen day is the min/max date.
- Preserves uniformity when no time weights are provided.
"""

import calendar
import random as _random
from datetime import date, datetime, time, timedelta

from datamimic_ce.domains.domain_core.base_literal_generator import BaseLiteralGenerator


class DateTimeGenerator(BaseLiteralGenerator):
    # Define mode of DateGenerator
    _CUSTOM_DATETIME_MODE = "custom"
    _RANDOM_DATETIME_MODE = "random"
    _CURRENT_DATETIME_MODE = "current"

    def __init__(
        self,
        min: str | None = None,
        max: str | None = None,
        value: str | None = None,
        random: bool | None = None,
        random_mode: bool | None = None,
        input_format: str | None = None,
        hour_weights: list[float] | None = None,
        minute_weights: list[float] | None = None,
        second_weights: list[float] | None = None,
        month_weights: list[float] | None = None,
        weekday_weights: list[float] | None = None,
        dom_weights: list[float] | None = None,
        # DSL sugar options
        months: str | list[int] | None = None,
        months_exclude: str | list[int] | None = None,
        weekdays: str | list[int | str] | None = None,
        dom: str | list[int | str] | None = None,
        hours_preset: str | None = None,
        minute_granularity: int | None = None,
        second_granularity: int | None = None,
        seed: int | None = None,
        rng: _random.Random | None = None,
    ):
        # Allow callers to inject their rng so rngSeed descriptors replay deterministically.
        self._rng = rng or _random.Random(seed)

        # format and weights
        self._input_format = input_format if input_format else "%Y-%m-%d %H:%M:%S"
        self._hour_weights = list(hour_weights) if hour_weights is not None else None
        self._minute_weights = list(minute_weights) if minute_weights is not None else None
        self._second_weights = list(second_weights) if second_weights is not None else None
        self._month_weights = list(month_weights) if month_weights is not None else None
        self._weekday_weights = list(weekday_weights) if weekday_weights is not None else None
        self._dom_weights = list(dom_weights) if dom_weights is not None else None

        # --- DSL sugar preprocessing: convert simple specs into weight lists when explicit weights are absent ---
        # Helper parsers
        def _parse_int_set_spec(spec: str, lo: int, hi: int) -> set[int]:
            parts = [p.strip() for p in spec.split(",") if p.strip()]
            out: set[int] = set()
            for p in parts:
                if "-" in p:
                    a, b = p.split("-", 1)
                    try:
                        a_i, b_i = int(a), int(b)
                    except ValueError as e:
                        raise ValueError(f"Invalid range '{p}' in spec '{spec}'") from e
                    if a_i > b_i:
                        a_i, b_i = b_i, a_i
                    for v in range(a_i, b_i + 1):
                        if not (lo <= v <= hi):
                            raise ValueError(f"Value {v} out of bounds [{lo},{hi}] in spec '{spec}'")
                        out.add(v)
                else:
                    try:
                        v = int(p)
                    except ValueError as e:
                        raise ValueError(f"Invalid value '{p}' in spec '{spec}'") from e
                    if not (lo <= v <= hi):
                        raise ValueError(f"Value {v} out of bounds [{lo},{hi}] in spec '{spec}'")
                    out.add(v)
            return out

        def _normalize_months(m: str | list[int] | None) -> set[int] | None:
            if m is None:
                return None
            if isinstance(m, list):
                s = set()
                for v in m:
                    if not (1 <= int(v) <= 12):
                        raise ValueError("months entries must be 1..12")
                    s.add(int(v))
                return s
            # Support tokens like Q1..Q4 as well as numeric ranges
            tokens = [tok.strip() for tok in m.split(",") if tok.strip()]
            out: set[int] = set()
            for tok in tokens:
                t = tok.upper()
                if t in {"Q1", "Q2", "Q3", "Q4"}:
                    if t == "Q1":
                        out |= {1, 2, 3}
                    elif t == "Q2":
                        out |= {4, 5, 6}
                    elif t == "Q3":
                        out |= {7, 8, 9}
                    elif t == "Q4":
                        out |= {10, 11, 12}
                    continue
                # fallback to numeric set spec, including ranges like 3-9
                out |= _parse_int_set_spec(t, 1, 12)
            return out

        def _normalize_weekdays(w: str | list[int | str] | None) -> set[int] | None:
            if w is None:
                return None
            name_to_idx = {
                "mon": 0,
                "tue": 1,
                "wed": 2,
                "thu": 3,
                "fri": 4,
                "sat": 5,
                "sun": 6,
            }
            special = {
                "weekend": {5, 6},
                "weekdays": {0, 1, 2, 3, 4},
                "business": {0, 1, 2, 3, 4},
                "workdays": {0, 1, 2, 3, 4},
                "all": {0, 1, 2, 3, 4, 5, 6},
            }

            def parse_token(tok: str) -> set[int]:
                t = tok.strip().lower()
                if not t:
                    return set()
                if t in special:
                    return set(special[t])
                if "-" in t:
                    a, b = t.split("-", 1)
                    if a not in name_to_idx or b not in name_to_idx:
                        raise ValueError(f"Invalid weekday range '{tok}'")
                    ai, bi = name_to_idx[a], name_to_idx[b]
                    if ai <= bi:
                        return set(range(ai, bi + 1))
                    # wrap-around, e.g., Fri-Mon
                    return set(list(range(ai, 7)) + list(range(0, bi + 1)))
                # single token: name or number
                if t in name_to_idx:
                    return {name_to_idx[t]}
                try:
                    vi = int(t)
                except ValueError:
                    raise ValueError(f"Invalid weekday token '{tok}'") from None
                if not (0 <= vi <= 6):
                    raise ValueError(f"Weekday index {vi} out of bounds [0,6]")
                return {vi}

            out: set[int] = set()
            if isinstance(w, list):
                for it in w:
                    if isinstance(it, int):
                        if not (0 <= it <= 6):
                            raise ValueError("weekday list values must be 0..6")
                        out.add(int(it))
                    elif isinstance(it, str):
                        out |= parse_token(it)
                    else:
                        raise ValueError("weekday list values must be ints or weekday names")
                return out
            # string
            for part in w.split(","):
                if part.strip():
                    out |= parse_token(part.strip())
            return out

        def _normalize_dom(d: str | list[int | str] | None) -> tuple[set[int] | None, bool]:
            if d is None:
                return None, False
            allow_last = False
            out: set[int] = set()

            def add_num(v: int):
                if not (1 <= v <= 31):
                    raise ValueError("dom values must be 1..31 or 'last'")
                out.add(v)

            if isinstance(d, list):
                for it in d:
                    if isinstance(it, int):
                        add_num(it)
                    elif isinstance(it, str) and it.strip().lower() == "last":
                        allow_last = True
                    else:
                        raise ValueError("dom list values must be ints or 'last'")
                return (out if out else None), allow_last
            # parse string like "1,3-5,last"
            for tok in [p.strip() for p in d.split(",") if p.strip()]:
                t = tok.lower()
                if t == "last":
                    allow_last = True
                    continue
                if "-" in t:
                    a, b = t.split("-", 1)
                    try:
                        ai, bi = int(a), int(b)
                    except ValueError as e:
                        raise ValueError(f"Invalid dom range '{tok}'") from e
                    if ai > bi:
                        ai, bi = bi, ai
                    for v in range(ai, bi + 1):
                        add_num(v)
                else:
                    try:
                        vi = int(t)
                    except ValueError as e:
                        raise ValueError(f"Invalid dom token '{tok}'") from e
                    add_num(vi)
            return (out if out else None), allow_last

        # Apply sugar for month/weekday/dom if explicit weights not provided
        inc_months = _normalize_months(months)
        exc_months = _normalize_months(months_exclude)
        if self._month_weights is None and (inc_months is not None or exc_months is not None):
            inc = inc_months if inc_months is not None else set(range(1, 13))
            if exc_months is not None:
                inc = inc - exc_months
            self._month_weights = [1.0 if (i + 1) in inc else 0.0 for i in range(12)]

        wk_allowed = _normalize_weekdays(weekdays)
        if self._weekday_weights is None and wk_allowed is not None:
            self._weekday_weights = [1.0 if i in wk_allowed else 0.0 for i in range(7)]

        dom_allowed, dom_allow_last = _normalize_dom(dom)
        # Store dom sugar as mask + flag; combined with dom_weights below
        self._dom_allowed_set = dom_allowed
        self._dom_allow_last = dom_allow_last

        # Time sugar presets/granularity
        if self._hour_weights is None and hours_preset:
            preset = hours_preset.strip().lower()
            if preset == "office":
                # 09-17 heavy, others light
                self._hour_weights = [0.1] * 24
                for h in range(9, 18):
                    self._hour_weights[h] = 1.0
            elif preset == "night":
                self._hour_weights = [0.0] * 24
                for h in list(range(0, 6)) + list(range(22, 24)):
                    self._hour_weights[h] = 1.0
            elif preset == "flat":
                # keep uniform by not setting weights
                self._hour_weights = None
            else:
                raise ValueError(f"Unknown hours_preset '{hours_preset}' (supported: office, night, flat)")

        def _granular(n: int, gran: int) -> list[float]:
            if gran <= 0 or gran > n:
                raise ValueError(f"granularity must be in 1..{n}")
            return [1.0 if i % gran == 0 else 0.0 for i in range(n)]

        if self._minute_weights is None and minute_granularity is not None:
            self._minute_weights = _granular(60, minute_granularity)
        if self._second_weights is None and second_granularity is not None:
            self._second_weights = _granular(60, second_granularity)

        # validate weights (length, non-negative, non-zero sum)
        def _validate_weights(w: list[float] | None, expected_len: int, name: str) -> list[float] | None:
            if w is None:
                return None
            if len(w) != expected_len:
                raise ValueError(f"{name} must have length {expected_len}")
            if any(v < 0 for v in w):
                raise ValueError(f"{name} must be non-negative")
            if sum(w) == 0:
                raise ValueError(f"{name} must not sum to zero")
            return w

        self._hour_weights = _validate_weights(self._hour_weights, 24, "hour_weights")
        self._minute_weights = _validate_weights(self._minute_weights, 60, "minute_weights")
        self._second_weights = _validate_weights(self._second_weights, 60, "second_weights")
        self._month_weights = _validate_weights(self._month_weights, 12, "month_weights")
        self._weekday_weights = _validate_weights(self._weekday_weights, 7, "weekday_weights")
        self._dom_weights = _validate_weights(self._dom_weights, 31, "dom_weights")

        # determine mode
        # Keep backward compatibility: "random" still supported; "random_mode" preferred internally.
        random_flag = bool(random_mode) if random_mode is not None else bool(random)

        # Handle custom (fixed) datetime value
        if value:
            self._result = datetime.strptime(value, self._input_format)
            self._mode = self._CUSTOM_DATETIME_MODE
            return

        # Handle random datetime (or bounded window)
        if random_flag or min or max:
            default_span = timedelta(days=int(365.25 * 50))
            self._min_dt = datetime.strptime(min, self._input_format) if min else None
            self._max_dt = datetime.strptime(max, self._input_format) if max else None

            if self._min_dt and self._max_dt and self._max_dt < self._min_dt:
                raise ValueError("max_datetime must be greater than or equal to min_datetime")

            if not self._min_dt and not self._max_dt:
                self._start_date = datetime.strptime("1970-01-01 00:00:00", self._input_format)
                self._time_difference = default_span
            elif self._min_dt and not self._max_dt:
                self._start_date = self._min_dt
                self._time_difference = default_span
            elif self._max_dt and not self._min_dt:
                self._start_date = self._max_dt - default_span
                self._time_difference = default_span
            else:
                self._start_date = self._min_dt  # type: ignore[assignment]
                self._time_difference = self._max_dt - self._min_dt  # type: ignore[operator]

            self._mode = self._RANDOM_DATETIME_MODE

            # Precompute month/day segments if any day-level weighting or sugar is provided
            if (
                self._month_weights is not None
                or self._weekday_weights is not None
                or self._dom_weights is not None
                or (hasattr(self, "_dom_allowed_set") and self._dom_allowed_set is not None)
                or (hasattr(self, "_dom_allow_last") and self._dom_allow_last)
            ):
                start_date = self._start_date.date()
                end_date = (self._start_date + self._time_difference).date()
                self._month_segments = self._compute_month_segments(start_date, end_date)
                self._month_choices, self._month_choice_weights = self._build_month_choice_distribution()
            return

        # Handle datetime.now()
        self._result = datetime.now()
        self._mode = self._CURRENT_DATETIME_MODE

    def generate(self) -> datetime | str:
        if self._mode != self._RANDOM_DATETIME_MODE:
            return self._result

        # Weighted day selection path (month/weekday/dom)
        if hasattr(self, "_month_choices"):
            y, m, days, day_weights = self._rng.choices(self._month_choices, weights=self._month_choice_weights, k=1)[0]
            chosen_day = self._rng.choices(days, weights=day_weights, k=1)[0]
            h, mi, se = self._sample_time_for_day(y, m, chosen_day.day)
            return datetime(y, m, chosen_day.day, h, mi, se)

        # No month weights: keep uniform base_result (guaranteed in bounds)
        base = self._uniform_base()
        if not (self._hour_weights or self._minute_weights or self._second_weights):
            return base

        y, m, d = base.year, base.month, base.day
        h, mi, se = self._sample_time_for_day(y, m, d)
        return datetime(y, m, d, h, mi, se)

    # ---------------- time sampling helpers ----------------
    def _uniform_base(self) -> datetime:
        total_seconds = int(self._time_difference.total_seconds())
        offset = self._rng.randint(0, total_seconds)
        return self._start_date + timedelta(seconds=offset)

    def _sample_time_for_day(self, y: int, m: int, d: int) -> tuple[int, int, int]:
        lo_h, lo_m, lo_s = 0, 0, 0
        hi_h, hi_m, hi_s = 23, 59, 59
        if hasattr(self, "_min_dt") and self._min_dt and date(y, m, d) == self._min_dt.date():
            t: time = self._min_dt.time()
            lo_h, lo_m, lo_s = t.hour, t.minute, t.second
        if hasattr(self, "_max_dt") and self._max_dt and date(y, m, d) == self._max_dt.date():
            t2: time = self._max_dt.time()
            hi_h, hi_m, hi_s = t2.hour, t2.minute, t2.second
        if (lo_h, lo_m, lo_s) > (hi_h, hi_m, hi_s):
            base_dt = self._uniform_base()
            return base_dt.hour, base_dt.minute, base_dt.second

        def _bounded_choice(n: int, weights: list[float] | None, lo: int, hi: int) -> int:
            if lo > hi:
                return self._rng.randint(0, n - 1)
            if weights is None:
                return self._rng.randint(lo, hi)
            masked = [weights[i] if lo <= i <= hi else 0.0 for i in range(n)]
            if sum(masked) == 0:
                return self._rng.randint(lo, hi)
            return self._rng.choices(range(n), weights=masked, k=1)[0]

        h = _bounded_choice(24, self._hour_weights, lo_h, hi_h)
        min_lo = lo_m if h == lo_h else 0
        min_hi = hi_m if h == hi_h else 59
        mi = _bounded_choice(60, self._minute_weights, min_lo, min_hi)

        sec_lo = lo_s if (h == lo_h and mi == min_lo) else 0
        sec_hi = hi_s if (h == hi_h and mi == min_hi) else 59
        se = _bounded_choice(60, self._second_weights, sec_lo, sec_hi)
        return h, mi, se

    def generate_date(self):
        return self.generate().date()

    # ---------------- helpers for month sampling ----------------
    @staticmethod
    def _ym_next(year: int, month: int) -> tuple[int, int]:
        return (year + (month == 12), 1 if month == 12 else month + 1)

    @staticmethod
    def _month_start_end(y: int, m: int) -> tuple[date, date]:
        last_day = calendar.monthrange(y, m)[1]
        return date(y, m, 1), date(y, m, last_day)

    def _compute_month_segments(self, dmin: date, dmax: date) -> dict[tuple[int, int], tuple[date, date]]:
        segs: dict[tuple[int, int], tuple[date, date]] = {}
        y, m = dmin.year, dmin.month
        end_y, end_m = dmax.year, dmax.month
        while True:
            ms, me = self._month_start_end(y, m)
            seg_start = max(ms, dmin)
            seg_end = min(me, dmax)
            if seg_start <= seg_end:
                segs[(y, m)] = (seg_start, seg_end)
            if (y, m) == (end_y, end_m):
                break
            y, m = self._ym_next(y, m)
        return segs

    def _build_month_choice_distribution(self) -> tuple[list[tuple[int, int, list[date], list[float]]], list[float]]:
        months: list[tuple[int, int, list[date], list[float]]] = []
        weights: list[float] = []
        for (y, m), (s, e) in self._month_segments.items():
            days: list[date] = []
            day_weights: list[float] = []
            cur = s
            while cur <= e:
                days.append(cur)
                # compute per-day weight
                mw = self._month_weights[m - 1] if self._month_weights else 1.0
                ww = self._weekday_weights[cur.weekday()] if self._weekday_weights else 1.0
                dom = cur.day
                dw = self._dom_weights[dom - 1] if self._dom_weights else 1.0
                # Apply DOM sugar masks (allowed set and/or 'last')
                allowed_set: set[int] | None = getattr(self, "_dom_allowed_set", None)
                if allowed_set is not None and dom not in allowed_set:
                    dw = 0.0
                if getattr(self, "_dom_allow_last", False) and dom != calendar.monthrange(y, m)[1]:
                    dw = 0.0
                day_weights.append(mw * ww * dw)
                cur = cur + timedelta(days=1)
            if not days:
                continue
            # filter out zero-weight days
            total_w = sum(day_weights)
            if total_w > 0:
                months.append((y, m, days, day_weights))
                weights.append(total_w)
        if not months:
            raise ValueError("No eligible dates within the range after applying month/weekday/dom weights.")
        return months, weights
