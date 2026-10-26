# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""The staffing rules that need more than one row: person suitability, seat search and the output check.

The model calls three functions, each with prepared rows and the policy; none reads a file:
``suitable_people`` (R1 to R3, once per position), ``assign_seats`` (R4 to R6, once per run) and
``check_position`` (the output check, once per position).
"""

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum
from typing import Any, TypedDict

Row = Mapping[str, Any]


class Rule(StrEnum):
    R1 = "R1"
    R2 = "R2"
    R3 = "R3"
    R4 = "R4"
    R5 = "R5"
    R6 = "R6"


class Outcome(StrEnum):
    COMPLETE = "complete"
    INFEASIBLE = "infeasible"
    BUDGET_EXHAUSTED = "budget_exhausted"


class Exclusion(TypedDict):
    person_id: int
    rule: Rule
    reason: str
    value: str | None


class Decision(TypedDict):
    position_id: str
    seat_id: str | None
    person_id: int | None
    action: str
    rule: Rule | None
    reason: str | None


@dataclass(frozen=True)
class Suitability:
    eligible: list[dict[str, int]]
    near_misses: list[Exclusion]
    excluded_by: dict[str, int]


@dataclass(frozen=True)
class Assignment:
    outcome: Outcome
    nodes: int
    backtracks: int
    seats: list[dict[str, Any]]
    unfilled_by: dict[str, int]
    decisions: list[Decision]


def _employment(person_id: int, company_id: str, function_id: str, employments: Sequence[Row]) -> Exclusion | None:
    jobs = [job for job in employments if job["person_id"] == person_id]
    if not jobs:
        return Exclusion(person_id=person_id, rule=Rule.R1, reason="no employment", value=None)
    at_company = [job for job in jobs if job["company_id"] == company_id]
    if not at_company:
        companies = ",".join(sorted(job["company_id"] for job in jobs))
        return Exclusion(person_id=person_id, rule=Rule.R1, reason="employed by another company", value=companies)
    if all(job["function_id"] != function_id for job in at_company):
        functions = ",".join(sorted(job["function_id"] for job in at_company))
        return Exclusion(person_id=person_id, rule=Rule.R1, reason="other function at this company", value=functions)
    return None


def _base_license(person_id: int, valid_on: date, person_licenses: Sequence[Row], policy: Row) -> Exclusion | None:
    licenses = [
        row
        for row in person_licenses
        if row["person_id"] == person_id and row["license_type"] == policy["base_license"]
    ]
    active = [row for row in licenses if row["status"] == policy["active_status"]]
    dated = [row for row in active if row["expires_on"] is not None]
    # The expiry date itself is still valid; a missing expiry is not unlimited validity.
    if any(date.fromisoformat(row["expires_on"]) >= valid_on for row in dated):
        return None
    if not licenses:
        return Exclusion(person_id=person_id, rule=Rule.R2, reason="no base license", value=None)
    if not active:
        return Exclusion(person_id=person_id, rule=Rule.R2, reason="base license inactive", value=None)
    if not dated:
        return Exclusion(person_id=person_id, rule=Rule.R2, reason="base license has no expiry date", value=None)
    latest = max(row["expires_on"] for row in dated)
    return Exclusion(person_id=person_id, rule=Rule.R2, reason="base license expired", value=latest)


def _qualification(
    person_id: int, function_id: str, person_qualifications: Sequence[Row], policy: Row
) -> Exclusion | None:
    required = policy["required_qualification"][function_id]
    if any(row["person_id"] == person_id and row["qualification_id"] == required for row in person_qualifications):
        return None
    return Exclusion(person_id=person_id, rule=Rule.R3, reason="missing qualification", value=required)


def suitable_people(
    company_id: str,
    function_id: str,
    valid_on: str,
    people: Sequence[Row],
    employments: Sequence[Row],
    person_licenses: Sequence[Row],
    person_qualifications: Sequence[Row],
    policy: Row,
) -> Suitability:
    """Decide R1 to R3 for every person and one position. Count each failed rule; name the near misses (one rule)."""
    on = date.fromisoformat(valid_on)
    eligible: list[dict[str, int]] = []
    near_misses: list[Exclusion] = []
    excluded_by: Counter[Rule] = Counter()
    for person in people:
        person_id = person["person_id"]
        checks = (
            _employment(person_id, company_id, function_id, employments),
            _base_license(person_id, on, person_licenses, policy),
            _qualification(person_id, function_id, person_qualifications, policy),
        )
        failures = [failure for failure in checks if failure is not None]
        excluded_by.update(failure["rule"] for failure in failures)
        if not failures:
            eligible.append({"person_id": person_id})
        elif len(failures) == 1:
            near_misses.append(failures[0])
    counts = {rule.value: excluded_by[rule] for rule in (Rule.R1, Rule.R2, Rule.R3)}
    return Suitability(eligible=eligible, near_misses=near_misses, excluded_by=counts)


def _conflict(held: Sequence[Row], position: Row) -> tuple[Rule, str] | None:
    for other in held:
        if other["position_id"] == position["position_id"]:
            return Rule.R4, "already holds a seat of this position"
        if other["approval_id"] != position["approval_id"] and (other["exclusive"] or position["exclusive"]):
            return Rule.R5, f"holds a seat of approval {other['approval_id']}; one of the two is exclusive"
        if other["company_id"] != position["company_id"]:
            return Rule.R6, f"holds a seat at company {other['company_id']}"
    return None


class _BudgetExhausted(Exception):
    pass


@dataclass
class _Search:
    seats: list[tuple[str, Row]]
    budget: int
    nodes: int = 0
    backtracks: int = 0
    held: dict[int, list[Row]] = field(default_factory=dict)
    chosen: dict[str, int] = field(default_factory=dict)
    dead_ends: Counter[Rule] = field(default_factory=Counter)
    decisions: list[Decision] = field(default_factory=list)

    def _forward_check(self, start: int) -> tuple[Row, set[Rule]] | None:
        """Return the first open position that has fewer free people than open seats, with the rules that took them."""
        open_seats = Counter(position["position_id"] for _, position in self.seats[start:])
        for position in {row["position_id"]: row for _, row in self.seats[start:]}.values():
            rules = set()
            free = 0
            for entry in position["eligible"]:
                conflict = _conflict(self.held.get(entry["person_id"], []), position)
                if conflict is None:
                    free += 1
                else:
                    rules.add(conflict[0])
            if free < open_seats[position["position_id"]]:
                return position, rules
        return None

    def fill(self, index: int) -> bool:
        """Depth-first: try the free people of one seat in order; undo a choice that leaves a later seat without one."""
        if index == len(self.seats):
            return True
        seat_id, position = self.seats[index]
        for entry in position["eligible"]:
            person_id = entry["person_id"]
            conflict = _conflict(self.held.get(person_id, []), position)
            if conflict is not None:
                self.decisions.append(_decision(position, seat_id, person_id, "skip", *conflict))
                continue
            self.nodes += 1
            if self.nodes > self.budget:
                raise _BudgetExhausted
            self.held.setdefault(person_id, []).append(position)
            self.chosen[seat_id] = person_id
            self.decisions.append(_decision(position, seat_id, person_id, "try"))
            starved = self._forward_check(index + 1)
            if starved is None and self.fill(index + 1):
                return True
            if starved is not None:
                blocked, rules = starved
                self.dead_ends.update(rules)
                reason = f"leaves {blocked['position_id']} without enough free people"
                for rule in sorted(rules):
                    self.decisions.append(_decision(position, seat_id, person_id, "dead_end", rule, reason))
            self.held[person_id].pop()
            del self.chosen[seat_id]
            self.backtracks += 1
            self.decisions.append(_decision(position, seat_id, person_id, "undo"))
        return False


def _decision(
    position: Row,
    seat_id: str | None,
    person_id: int | None,
    action: str,
    rule: Rule | None = None,
    reason: str | None = None,
) -> Decision:
    return Decision(
        position_id=position["position_id"],
        seat_id=seat_id,
        person_id=person_id,
        action=action,
        rule=rule,
        reason=reason,
    )


def _shortages(positions: Sequence[Row]) -> tuple[Counter[Rule], list[Decision]]:
    """A position with fewer eligible people than seats is infeasible without search; name the blocking rules."""
    blocked: Counter[Rule] = Counter()
    decisions: list[Decision] = []
    for position in positions:
        eligible, seats = len(position["eligible"]), position["seats"]
        if eligible >= seats:
            continue
        if eligible:
            blocked[Rule.R4] += 1
            decisions.append(
                _decision(position, None, None, "short", Rule.R4, f"{eligible} eligible people for {seats} seats")
            )
        for miss in position["near_misses"]:
            rule = Rule(miss["rule"])
            blocked[rule] += 1
            reason = miss["reason"] if miss["value"] is None else f"{miss['reason']} ({miss['value']})"
            decisions.append(_decision(position, None, miss["person_id"], "short", rule, reason))
    return blocked, decisions


def _by_rule(counts: Counter[Rule]) -> dict[str, int]:
    return {rule.value: counts[rule] for rule in Rule}


def assign_seats(positions: Sequence[Row], policy: Row) -> Assignment:
    """Fill the most constrained positions first, then company by company and function by function."""
    blocked, shortage = _shortages(positions)
    if blocked:
        return Assignment(Outcome.INFEASIBLE, 0, 0, [], _by_rule(blocked), shortage)
    ordered = sorted(
        positions, key=lambda row: (len(row["eligible"]), row["company_id"], row["function_id"], row["version_id"])
    )
    seats = [(f"{row['position_id']}-{number}", row) for row in ordered for number in range(1, row["seats"] + 1)]
    search = _Search(seats=seats, budget=policy["search_budget"])
    try:
        complete = search.fill(0)
    except _BudgetExhausted:
        return Assignment(
            Outcome.BUDGET_EXHAUSTED, search.budget, search.backtracks, [], _by_rule(Counter()), search.decisions
        )
    if not complete:
        return Assignment(
            Outcome.INFEASIBLE, search.nodes, search.backtracks, [], _by_rule(search.dead_ends), search.decisions
        )
    plan = [
        {
            "seat_id": seat_id,
            "version_id": row["version_id"],
            "function_id": row["function_id"],
            "person_id": search.chosen[seat_id],
        }
        for seat_id, row in seats
    ]
    return Assignment(Outcome.COMPLETE, search.nodes, search.backtracks, plan, _by_rule(Counter()), search.decisions)


def check_position(position: Row, plan: Sequence[Row], positions: Sequence[Row]) -> dict[str, Any]:
    """Check the plan for one position without the search: R1 to R3 by the eligible list, R4 to R6 directly."""
    by_seat = {(row["version_id"], row["function_id"]): row for row in positions}
    key = (position["version_id"], position["function_id"])
    people = [row["person_id"] for row in plan if (row["version_id"], row["function_id"]) == key]
    eligible = {entry["person_id"] for entry in position["eligible"]}
    others = [by_seat[(row["version_id"], row["function_id"])] for row in plan if row["person_id"] in people]
    return {
        "filled": len(people),
        "all_eligible": all(person in eligible for person in people),
        "distinct_people": len(set(people)) == len(people),
        "approval_exclusive": all(
            other["approval_id"] == position["approval_id"]
            for other in others
            if position["exclusive"] or other["exclusive"]
        ),
        "company_exclusive": all(other["company_id"] == position["company_id"] for other in others),
    }
