# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""The global search of the shift roster: staff every slot at its minimum so that RS2 to RS5 hold.

Depth-first search over the slots in time order, with backtracking and a forward check. The order is fixed (slot
start, then ward; staff by id), so the same inputs give the same plan. A greedy pass is the first descent of this
search: one backtrack means that the greedy pass fails.
"""

import datetime  # the module, as scripts see it: a library name shadows the script global of the same name
from collections.abc import Mapping, Sequence
from enum import StrEnum
from itertools import combinations

Row = Mapping[str, object]


class Outcome(StrEnum):
    SOLVED = "solved"
    INFEASIBLE = "infeasible"
    BUDGET_EXHAUSTED = "budget_exhausted"
    NOT_RUN = "not_run"


class Rule(StrEnum):
    REST = "RS2"
    HOURS = "RS3"
    AT_MAXIMUM = "RS4"
    ONE_WARD = "RS5"
    NOT_NEEDED = "not_needed"  # no rule excludes the person; the slot has its minimum staff


def plan_roster(
    slots: Sequence[Row], candidates: Sequence[Row], min_rest_hours: int | None, search_budget: int | None
) -> dict[str, object]:
    """Return the plan (``entries``), the outcome with its message, the search counters and, per slot, why each
    suitable person who is not assigned was left out (``decisions``). A parameter is None when the policy file does
    not give a whole number; then the search does not run, and the policy checks name the parameter."""
    if min_rest_hours is None or search_budget is None:
        message = "the search did not run: min_rest_hours or search_budget is not a whole number"
        return _result(Outcome.NOT_RUN, message, 0, 0, [], [])
    order = sorted(slots, key=lambda slot: (slot["starts_at"], slot["ward_id"]))
    pool = {
        slot["slot_id"]: sorted(
            (
                candidate
                for candidate in candidates
                if candidate["shift_date"] == slot["shift_date"] and slot["shift_code"] in candidate["eligible_shifts"]
            ),
            key=lambda candidate: candidate["staff_id"],
        )
        for slot in order
    }
    rest = datetime.timedelta(hours=min_rest_hours)
    shifts: dict[object, list[Row]] = {candidate["staff_id"]: [] for candidate in candidates}
    teams: dict[object, tuple[Row, ...]] = {}
    steps = backtracks = 0
    stopped_at: Row | None = None

    def week(row: Row) -> tuple[int, int]:
        """The ISO year and week of the shift start; a shift counts fully in that week."""
        return row["starts_at"].isocalendar()[:2]

    def blocker(candidate: Row, slot: Row) -> tuple[Rule, str] | None:
        """The strongest rule that forbids this person the slot, given the shifts the person already has: rest and
        overlap (RS2) first, then one ward per day (RS5), then the weekly hours (RS3)."""
        worked = shifts[candidate["staff_id"]]
        for other in worked:
            gap = max(slot["starts_at"] - other["ends_at"], other["starts_at"] - slot["ends_at"])
            if gap < rest:
                return Rule.REST, f"{gap.total_seconds() / 3600:g} h from {other['slot_id']}, needs {min_rest_hours} h"
        hours = slot["hours"] + sum(other["hours"] for other in worked if week(other) == week(slot))
        if hours > candidate["max_weekly_hours"]:
            iso_week = slot["starts_at"].strftime("%G-W%V")
            return Rule.HOURS, f"{hours} h in ISO week {iso_week}, contract allows {candidate['max_weekly_hours']} h"
        return None

    def available(slot: Row) -> list[Row]:
        """The people who may still take the slot, those with the fewest hours first, then by id."""
        free = [candidate for candidate in pool[slot["slot_id"]] if blocker(candidate, slot) is None]
        return sorted(free, key=lambda candidate: sum(other["hours"] for other in shifts[candidate["staff_id"]]))

    def leads(team: Sequence[Row], slot: Row) -> int:
        return sum(slot["lead_cert"] in candidate["valid_certs"] for candidate in team)

    def shortage(slot: Row) -> str | None:
        """Forward check: why the slot cannot be staffed any more, or None."""
        free = available(slot)
        if len(free) < slot["min_staff"] or leads(free, slot) < slot["min_lead"]:
            return (
                f"slot {slot['slot_id']} has {len(free)} suitable staff (needs {slot['min_staff']}) and "
                f"{leads(free, slot)} holders of {slot['lead_cert']} (needs {slot['min_lead']})"
            )
        return None

    def solve(index: int) -> bool | None:
        """True: every later slot is staffed; False: no team works (a proof); None: the budget ran out."""
        nonlocal steps, backtracks, stopped_at
        if index == len(order):
            return True
        slot = order[index]
        for team in combinations(available(slot), slot["min_staff"]):
            if steps == search_budget:
                stopped_at = slot
                return None
            steps += 1
            if leads(team, slot) < slot["min_lead"]:
                continue
            teams[slot["slot_id"]] = team
            for member in team:
                shifts[member["staff_id"]].append(slot)
            if all(shortage(later) is None for later in order[index + 1 :]):
                solved = solve(index + 1)
                if solved is not False:
                    return solved
            for member in team:
                shifts[member["staff_id"]].remove(slot)
            del teams[slot["slot_id"]]
            backtracks += 1
        return False

    proof = next((reason for reason in map(shortage, order) if reason is not None), None)
    solved = False if proof is not None else solve(0)
    if solved is True:
        outcome, message = Outcome.SOLVED, f"every slot is staffed after {steps} steps and {backtracks} backtracks"
    elif solved is None and stopped_at is not None:
        outcome = Outcome.BUDGET_EXHAUSTED
        message = (
            f"the search stopped at slot {stopped_at['slot_id']} after {steps} steps, the search_budget; "
            "no roster was found, and this does not prove that none exists"
        )
    else:
        outcome = Outcome.INFEASIBLE
        message = f"no roster exists: {proof or f'every team for every slot fails after {steps} steps'}"
    entries = []
    decisions = []
    for slot in order if outcome is Outcome.SOLVED else ():
        team = teams[slot["slot_id"]]
        assigned = [member["staff_id"] for member in team]
        entries += [
            {
                "entry_id": len(entries) + position + 1,
                "slot_id": slot["slot_id"],
                "shift_date": slot["shift_date"],
                "ward_id": slot["ward_id"],
                "shift_code": slot["shift_code"],
                "staff_id": staff_id,
            }
            for position, staff_id in enumerate(assigned)
        ]
        blocked = []
        for candidate in pool[slot["slot_id"]]:
            if candidate["staff_id"] in assigned:
                continue
            rule, reason = blocker(candidate, slot) or (
                (Rule.AT_MAXIMUM, f"the slot has its maximum of {slot['max_staff']} staff")
                if slot["min_staff"] == slot["max_staff"]
                else (Rule.NOT_NEEDED, f"the slot has its minimum of {slot['min_staff']} staff")
            )
            blocked.append({"staff_id": candidate["staff_id"], "rule": rule.value, "reason": reason})
        decisions.append({"slot_id": slot["slot_id"], "assigned": assigned, "blocked": blocked})
    return _result(outcome, message, steps, backtracks, entries, decisions)


def _result(
    outcome: Outcome, message: str, steps: int, backtracks: int, entries: list[Row], decisions: list[Row]
) -> dict[str, object]:
    # A row holds plain values, so the enum leaves as its value.
    return {
        "outcome": outcome.value,
        "search_complete": outcome in (Outcome.SOLVED, Outcome.INFEASIBLE),
        "message": message,
        "steps": steps,
        "backtracks": backtracks,
        "entries": entries,
        "decisions": decisions,
    }
