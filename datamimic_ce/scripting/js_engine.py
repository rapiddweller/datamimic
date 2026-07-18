# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""PROTOTYPE - JS execution spike, not wired into the DSL/parser yet.

Evaluates `{js:...}`-style inline scripts (Benerator descriptor parity) via an embedded V8
(mini-racer, optional dependency - `pip install datamimic_ce[js]`).

The hard part isn't "can we eval JS" - it's that a JS engine ships nondeterministic builtins
(Math.random, Date.now/new Date) inside a deterministic-first engine (AGENTS.md rule 6: same
seed -> same output). Bridging Math.random through a Python callback per call is possible (mini-
racer's wrap_py_function) but async-only, which doesn't fit CE's synchronous evaluation model.
Instead: derive ONE seed from CE's own RNG chain (spawn_rng/derive_child_seed, the same helper
BaseDomainGenerator._derive_rng uses) and seed a small pure-JS PRNG (Mulberry32) with it - no
Python<->JS bridge needed per call, just one integer at construction time. Date.now is pinned to
the same DETERMINISTIC_ANCHOR every other "now"-derived field in CE already uses.

Unseeded (no rng passed): left alone, native Math.random/Date.now - matches "no rngSeed = every
run differs, by design".

Known gap, not solved by this prototype: `new Date()` (argument-less) still reads real wall-clock
- only `Date.now()` is pinned. Fine for a feasibility spike; would need closing before real use.
"""

from __future__ import annotations

from datetime import UTC
from random import Random
from typing import Any

from datamimic_ce.domains.domain_core.runtime.clock import DETERMINISTIC_ANCHOR
from datamimic_ce.domains.domain_core.runtime.rng import derive_child_seed

_SEEDED_BOOTSTRAP = """
(function(seed, fixedNowMs) {
    let state = seed >>> 0;
    Math.random = function() {
        state = (state + 0x6D2B79F5) | 0;
        let t = Math.imul(state ^ (state >>> 15), 1 | state);
        t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
        return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
    Date.now = function() { return fixedNowMs; };
})(%d, %d);
"""


class JsEngine:
    """A JS evaluation context. Pass `rng` for deterministic Math.random/Date.now; omit for a
    normal (non-reproducible) engine."""

    def __init__(self, rng: Random | None = None) -> None:
        from py_mini_racer import MiniRacer

        self._ctx = MiniRacer()
        if rng is not None:
            seed = derive_child_seed(rng)
            # DETERMINISTIC_ANCHOR is naive; anchor it to UTC explicitly so the epoch-ms value
            # is the same on every machine regardless of local timezone.
            fixed_now_ms = int(DETERMINISTIC_ANCHOR.replace(tzinfo=UTC).timestamp() * 1000)
            self._ctx.eval(_SEEDED_BOOTSTRAP % (seed, fixed_now_ms))

    def eval(self, expr: str) -> Any:
        return self._ctx.eval(expr)
