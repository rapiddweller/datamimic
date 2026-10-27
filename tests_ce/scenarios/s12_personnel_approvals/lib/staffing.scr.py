# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""The staffing rules that need more than one row: person suitability and the seat search.

Each step reads the policy through ``read_policy``. The model calls two functions with prepared rows and the
policy; none reads a file: ``suitable_people`` (R1 to R3, once per position) and ``assign_seats`` (R4 to R6, once
per run). The output check of step 4 is XML.
"""

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum
from typing import Any, TypedDict

Row = Mapping[str, Any]


class Rule(StrEnum):
    # R1 has three parts: the employment must name the person, the company and the function.
    R1_PERSON = "R1_person"
    R1_COMPANY = "R1_company"
    R1_FUNCTION = "R1_function"
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
class Policy:
    base_license: str
    active_status: str
    required_qualification: dict[str, str]
    max_seats: int
    exclusive_approvals: tuple[str, ...]
    search_budget: int


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
    skipped_by: dict[str, int]
    decisions: list[Decision]


def read_policy(row: Row) -> Policy:
    """Check the type of each rule parameter: a text where a list of ids belongs would still match by substring."""
    for name in ("base_license", "active_status"):
        if not isinstance(row[name], str):
            raise TypeError(f"policy {name} must be a text")
    for name in ("max_seats", "search_budget"):
        if not isinstance(row[name], int) or isinstance(row[name], bool):
            raise TypeError(f"policy {name} must be an integer")
    exclusive = row["exclusive_approvals"]
    if not isinstance(exclusive, list) or not all(isinstance(item, str) for item in exclusive):
        raise TypeError("policy exclusive_approvals must be a list of approval ids")
    # A row's mapping has keys and item access only (DotableDict), so copy it by key.
    required = {key: row["required_qualification"][key] for key in row["required_qualification"]}
    if not all(isinstance(item, str) for item in required.values()):
        raise TypeError("policy required_qualification must map function ids to qualification ids")
    return Policy(
        base_license=row["base_license"],
        active_status=row["active_status"],
        required_qualification=required,
        max_seats=row["max_seats"],
        exclusive_approvals=tuple(exclusive),
        search_budget=row["search_budget"],
    )


def _position_key(row: Row) -> tuple[str, str]:
    """R4 names a position by version and function, not by the id of its demand row."""
    return row["version_id"], row["function_id"]


def _employment(person_id: int, company_id: str, function_id: str, employments: Sequence[Row]) -> Exclusion | None:
    jobs = [job for job in employments if job["person_id"] == person_id]
    if not jobs:
        return Exclusion(person_id=person_id, rule=Rule.R1_PERSON, reason="no employment", value=None)
    at_company = [job for job in jobs if job["company_id"] == company_id]
    if not at_company:
        companies = ",".join(sorted(job["company_id"] for job in jobs))
        return Exclusion(
            person_id=person_id, rule=Rule.R1_COMPANY, reason="employed by another company", value=companies
        )
    if all(job["function_id"] != function_id for job in at_company):
        functions = ",".join(sorted(job["function_id"] for job in at_company))
        return Exclusion(
            person_id=person_id, rule=Rule.R1_FUNCTION, reason="other function at this company", value=functions
        )
    return None


def _base_license(person_id: int, valid_on: date, person_licenses: Sequence[Row], policy: Policy) -> Exclusion | None:
    licenses = [
        row for row in person_licenses if row["person_id"] == person_id and row["license_type"] == policy.base_license
    ]
    active = [row for row in licenses if row["status"] == policy.active_status]
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
    return Exclusion(person_id=person_id, rule=Rule.R2, reason="base license expired", value=f"{latest} < {valid_on}")


def _qualification(
    person_id: int, function_id: str, person_qualifications: Sequence[Row], policy: Policy
) -> Exclusion | None:
    required = policy.required_qualification[function_id]
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
    policy: Policy,
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
    return Suitability(eligible=eligible, near_misses=near_misses, excluded_by=_by_rule(excluded_by))


def _conflict(held: Sequence[Row], position: Row) -> tuple[Rule, str] | None:
    for other in held:
        if _position_key(other) == _position_key(position):
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
    skipped: Counter[Rule] = field(default_factory=Counter)
    decisions: list[Decision] = field(default_factory=list)

    def _forward_check(self, start: int) -> tuple[Row, set[Rule]] | None:
        """Return the first open position that has fewer free people than open seats, with the rules that took them."""
        open_seats = Counter(_position_key(position) for _, position in self.seats[start:])
        for position in {_position_key(row): row for _, row in self.seats[start:]}.values():
            rules = set()
            free = 0
            for entry in position["eligible"]:
                conflict = _conflict(self.held.get(entry["person_id"], []), position)
                if conflict is None:
                    free += 1
                else:
                    rules.add(conflict[0])
            if free < open_seats[_position_key(position)]:
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
                self.skipped[conflict[0]] += 1
                self.decisions.append(_decision(position, seat_id, person_id, "skip", *conflict))
                continue
            self.nodes += 1
            if self.nodes > self.budget:
                raise _BudgetExhausted
            self.held.setdefault(person_id, []).append(position)
            self.chosen[seat_id] = person_id
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
        causes: list[Decision] = []
        if eligible:
            causes.append(_decision(position, None, None, "short", Rule.R4, f"{eligible} eligible for {seats} seats"))
        for miss in position["near_misses"]:
            reason = miss["reason"] if miss["value"] is None else f"{miss['reason']} ({miss['value']})"
            causes.append(_decision(position, None, miss["person_id"], "short", Rule(miss["rule"]), reason))
        # People of other companies always miss R1; they are the cause only when no closer cause exists.
        closer = [cause for cause in causes if cause["rule"] != Rule.R1_COMPANY]
        for cause in closer or causes:
            blocked[Rule(cause["rule"])] += 1
            decisions.append(cause)
    return blocked, decisions


def _by_rule(counts: Counter[Rule]) -> dict[str, int]:
    return {rule.value: counts[rule] for rule in Rule}


def assign_seats(positions: Sequence[Row], policy: Policy) -> Assignment:
    """Fill the most constrained positions first, then company by company and function by function."""
    blocked, shortage = _shortages(positions)
    if blocked:
        return Assignment(Outcome.INFEASIBLE, 0, 0, [], _by_rule(blocked), _by_rule(Counter()), shortage)
    ordered = sorted(
        positions, key=lambda row: (len(row["eligible"]), row["company_id"], row["function_id"], row["version_id"])
    )
    seats = [(f"{row['position_id']}-{number}", row) for row in ordered for number in range(1, row["seats"] + 1)]
    search = _Search(seats=seats, budget=policy.search_budget)
    try:
        complete = search.fill(0)
    except _BudgetExhausted:
        skipped_by = _by_rule(search.skipped)
        unfilled_by = _by_rule(Counter())
        return Assignment(
            Outcome.BUDGET_EXHAUSTED, search.budget, search.backtracks, [], unfilled_by, skipped_by, search.decisions
        )
    skipped_by = _by_rule(search.skipped)
    if not complete:
        unfilled_by = _by_rule(search.dead_ends)
        return Assignment(
            Outcome.INFEASIBLE, search.nodes, search.backtracks, [], unfilled_by, skipped_by, search.decisions
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
    return Assignment(
        Outcome.COMPLETE, search.nodes, search.backtracks, plan, _by_rule(Counter()), skipped_by, search.decisions
    )
