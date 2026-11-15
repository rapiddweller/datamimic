# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""The global allocation of stock lots to orders: fill every order that does not allow a partial shipment completely
(A2, A4, A5), then ship what remains to the partial orders.

Depth-first search over the must-fill orders (ship date, then id) with backtracking and a forward check. For each order
the search tries the lot sets (at most ``max_lots_per_order`` lots) in order of expiry; the lot set is filled from its
first lot to its last. The order is fixed, so the same inputs give the same allocation. Which lots may serve an order
(A1, A3) is decided before the search, by the ``eligible_lots`` of each order.
"""

from collections.abc import Mapping, Sequence
from enum import StrEnum
from itertools import combinations

Row = Mapping[str, object]


class Outcome(StrEnum):
    SOLVED = "solved"
    INFEASIBLE = "infeasible"
    BUDGET_EXHAUSTED = "budget_exhausted"


class Reason(StrEnum):
    NO_STOCK = "A2"
    LOT_LIMIT = "A5"
    NOT_NEEDED = "not_needed"  # stock is left, the order has its quantity
    USED = "used"


def allocate_orders(
    orders: Sequence[Row], lots: Sequence[Row], max_lots_per_order: int, search_budget: int
) -> dict[str, object]:
    """Return the allocation lines (``entries``), the outcome with its message, the search counters and, per order and
    eligible lot, whether the lot was used and why not (``decisions``)."""
    key = lambda order: (order["ship_on"], order["order_id"])  # noqa: E731
    must = sorted((order for order in orders if order["allow_partial"] == "no"), key=key)
    partial = sorted((order for order in orders if order["allow_partial"] != "no"), key=key)
    by_id = {lot["lot_id"]: lot for lot in lots}
    left = {lot["lot_id"]: lot["quantity"] for lot in lots}
    steps = backtracks = 0
    stopped_at: Row | None = None
    taken: dict[str, list[tuple[str, int]]] = {}

    def fill(order: Row, chosen: Sequence[str]) -> list[tuple[str, int]]:
        need, lines = order["quantity"], []
        for lot_id in chosen:
            part = min(need, left[lot_id])
            if part:
                lines.append((lot_id, part))
                need -= part
        return lines

    def sets(order: Row) -> list[tuple[str, ...]]:
        """The lot sets that fill the whole order now, with the earliest expiry first."""
        eligible = sorted(order["eligible_lots"], key=lambda lot_id: (by_id[lot_id]["expires_on"], lot_id))
        return [
            chosen
            for size in range(1, max_lots_per_order + 1)
            for chosen in combinations(eligible, size)
            if sum(left[lot_id] for lot_id in chosen) >= order["quantity"]
        ]

    def solve(index: int) -> bool | None:
        """True: every later order is filled; False: no allocation works (a proof); None: the budget ran out."""
        nonlocal steps, backtracks, stopped_at
        if index == len(must):
            return True
        order = must[index]
        for chosen in sets(order):
            if steps == search_budget:
                stopped_at = order
                return None
            steps += 1
            lines = fill(order, chosen)
            for lot_id, part in lines:
                left[lot_id] -= part
            taken[order["order_id"]] = lines
            if all(sets(later) for later in must[index + 1 :]):
                solved = solve(index + 1)
                if solved is not False:
                    return solved
            for lot_id, part in lines:
                left[lot_id] += part
            del taken[order["order_id"]]
            backtracks += 1
        return False

    proof = next((order["order_id"] for order in must if not sets(order)), None)
    solved = False if proof is not None else solve(0)
    if solved is True:
        outcome, message = Outcome.SOLVED, f"every order is filled after {steps} steps and {backtracks} backtracks"
    elif solved is None and stopped_at is not None:
        outcome = Outcome.BUDGET_EXHAUSTED
        message = (
            f"the search stopped at order {stopped_at['order_id']} after {steps} steps, the search_budget; "
            "no allocation was found, and this does not prove that none exists"
        )
    else:
        outcome = Outcome.INFEASIBLE
        message = (
            f"no allocation exists: order {proof} cannot be filled from {max_lots_per_order} lots at most"
            if proof is not None
            else f"no allocation exists: every lot set for every order fails after {steps} steps"
        )
    entries: list[Row] = []
    decisions: list[Row] = []
    if outcome is Outcome.SOLVED:
        left.update({lot["lot_id"]: lot["quantity"] for lot in lots})  # replay: a reason sees only earlier orders
        for order in must + partial:
            if order["allow_partial"] != "no":  # the remaining stock, earliest expiry first, up to the lot limit
                eligible = sorted(order["eligible_lots"], key=lambda lot_id: (by_id[lot_id]["expires_on"], lot_id))
                lines = fill(order, [lot_id for lot_id in eligible if left[lot_id]][:max_lots_per_order])
            else:
                lines = taken[order["order_id"]]
            used = {lot_id for lot_id, _ in lines}
            lots_seen = []
            for lot_id in sorted(order["eligible_lots"], key=lambda item: (by_id[item]["expires_on"], item)):
                if lot_id in used:
                    lots_seen.append({"lot_id": lot_id, "reason": Reason.USED.value, "detail": "used"})
                elif not left[lot_id]:
                    lots_seen.append({"lot_id": lot_id, "reason": Reason.NO_STOCK.value, "detail": "no quantity left"})
                elif order["allow_partial"] != "no":
                    lots_seen.append(
                        {"lot_id": lot_id, "reason": Reason.LOT_LIMIT.value, "detail": "the order has its lots limit"}
                    )
                else:
                    lots_seen.append(
                        {"lot_id": lot_id, "reason": Reason.NOT_NEEDED.value, "detail": "the order has its quantity"}
                    )
            for lot_id, part in lines:
                left[lot_id] -= part
                entries.append(
                    {
                        "allocation_id": f"A{len(entries) + 1:02d}",
                        "order_id": order["order_id"],
                        "lot_id": lot_id,
                        "quantity": part,
                    }
                )
            decisions.append({"order_id": order["order_id"], "lots": lots_seen})
    return {
        "outcome": outcome.value,
        "search_complete": outcome in (Outcome.SOLVED, Outcome.INFEASIBLE),
        "message": message,
        "steps": steps,
        "backtracks": backtracks,
        "entries": entries,
        "decisions": decisions,
    }
