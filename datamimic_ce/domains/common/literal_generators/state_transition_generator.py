# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from __future__ import annotations

import random
from collections.abc import Iterable
from dataclasses import dataclass

from datamimic_ce.domains.domain_core.base_literal_generator import BaseLiteralGenerator

# One transition: (from_state, to_state, weight)
Rule = tuple[str, str, float]


@dataclass(frozen=True)
class StateMachineDef:
    """A reusable <state-machine> definition stored under its id in the context, so
    each ``generator="<id>"`` reference builds its own (stateful) generator."""

    rules: tuple[Rule, ...]
    start: str | None = None


def _parse_spec(spec: str) -> list[Rule]:
    """Parse the inline string form into rules: ``from->to[:weight]`` comma-separated."""
    rules: list[Rule] = []
    for raw in spec.split(","):
        rule = raw.strip()
        if not rule:
            continue
        if "->" not in rule:
            raise ValueError(f"invalid transition '{rule}', expected 'from->to[:weight]'")
        src_part, _, rest = rule.partition("->")
        tgt_part, _, weight_part = rest.partition(":")
        src, tgt = src_part.strip(), tgt_part.strip()
        try:
            weight = float(weight_part) if weight_part.strip() else 1.0
        except ValueError as e:
            raise ValueError(f"invalid weight in transition '{rule}': {weight_part!r}") from e
        rules.append((src, tgt, weight))
    return rules


def _index_rules(rules: Iterable[Rule]) -> tuple[dict[str, tuple[list[str], list[float]]], str]:
    """Build ``{from: (targets, weights)}`` and resolve the start (first rule's source)."""
    transitions: dict[str, tuple[list[str], list[float]]] = {}
    start: str | None = None
    for src, tgt, weight in rules:
        if not src or not tgt:
            raise ValueError(f"invalid transition '{src}->{tgt}', from/to must be non-empty")
        if weight <= 0:
            raise ValueError(f"transition '{src}->{tgt}' weight must be > 0, got {weight}")
        if start is None:
            start = src
        targets, weights = transitions.setdefault(src, ([], []))
        targets.append(tgt)
        weights.append(weight)
    if start is None:
        raise ValueError("StateTransitionGenerator needs at least one 'from->to' transition")
    return transitions, start


class StateTransitionGenerator(BaseLiteralGenerator):
    """Walk a weighted state machine, emitting one state per ``generate()`` call.

    The next state depends on the current one (Markov property), so a sequence of
    calls produces a realistic lifecycle path (order/payment/claim status) — unlike
    independent weighted values which cannot express "after 'paid' comes 'shipped'
    90% / 'cancelled' 10%".

    Construct from the inline string form (DSL ``generator="StateTransitionGenerator('a->b, b->c:0.5')"``)
    or from structured rules (the ``<state-machine>`` element). In both cases:
    - start = the first rule's source unless ``start`` is given
    - a state with no outgoing transition is terminal: it is emitted, then the
      next call restarts the walk at the start state
    """

    # Stateful (holds the current position) — keep one instance per statement.
    cache_in_root = False

    def __init__(
        self,
        transitions: str | Iterable[Rule],
        *,
        start: str | None = None,
        rng: random.Random | None = None,
    ) -> None:
        super().__init__(rng=rng)
        rules = _parse_spec(transitions) if isinstance(transitions, str) else list(transitions)
        self._transitions, first = _index_rules(rules)
        self._start = start if start is not None else first
        self._current = self._start

    def generate(self) -> str:
        state = self._current
        edges = self._transitions.get(state)
        if edges is None:
            # terminal state: emit it, restart the walk on the next call
            self._current = self._start
        else:
            targets, weights = edges
            self._current = self._rng.choices(targets, weights=weights, k=1)[0]
        return state
