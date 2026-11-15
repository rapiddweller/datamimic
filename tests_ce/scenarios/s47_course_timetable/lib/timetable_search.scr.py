# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""The global search of the course timetable: place every session of every course in a slot and a room so that
T2 to T6 hold.

Depth-first search over the sessions (course id, then number) with backtracking and a forward check: a placement is
undone when a later session has no slot and room left. The order is fixed (slots and rooms in file order), so the same
inputs give the same timetable.
"""

from collections.abc import Mapping, Sequence
from enum import StrEnum
from itertools import product

Row = Mapping[str, object]


class Outcome(StrEnum):
    SOLVED = "solved"
    INFEASIBLE = "infeasible"
    BUDGET_EXHAUSTED = "budget_exhausted"


class Rule(StrEnum):
    CAPACITY = "T2"
    TEACHER = "T3"
    ROOM = "T4"
    STUDENT = "T5"
    ONE_PER_DAY = "T6"
    UNDONE = "undone"  # no rule refuses the place; the search tried it and undid the choice


def plan_timetable(
    courses: Sequence[Row],
    rooms: Sequence[Row],
    slots: Sequence[Row],
    unavailable: Sequence[Row],
    admitted: Mapping[str, Sequence[str]],
    search_budget: int,
) -> dict[str, object]:
    """Return the sessions (``entries``), the outcome with its message, the search counters and, per session, the
    places before the chosen one that the session did not get, with the rule and the reason (``decisions``)."""
    pending = [
        (course, number)
        for course in sorted(courses, key=lambda course: course["course_id"])
        for number in range(1, course["sessions"] + 1)
    ]
    off = {(row["teacher_id"], row["slot_id"]) for row in unavailable}
    placed: list[dict[str, object]] = []
    steps = backtracks = 0
    stopped_at: tuple[Row, int] | None = None

    def refusal(course: Row, slot: Row, room: Row) -> tuple[Rule, str] | None:
        """The strongest rule that refuses this place, given the sessions already placed: capacity (T2), the
        teacher (T3), the room (T4), a student in two places (T5), then two sessions of a course on one day (T6)."""
        headcount = len(admitted[course["course_id"]])
        if room["capacity"] < headcount:
            return Rule.CAPACITY, f"room {room['room_id']} holds {room['capacity']}, the course has {headcount}"
        if (course["teacher_id"], slot["slot_id"]) in off:
            return Rule.TEACHER, f"{course['teacher_id']} is unavailable in {slot['slot_id']}"
        for other in placed:
            if other["slot_id"] != slot["slot_id"]:
                continue
            if other["teacher_id"] == course["teacher_id"]:
                return Rule.TEACHER, f"{course['teacher_id']} teaches {other['course_id']} in {slot['slot_id']}"
            if other["room_id"] == room["room_id"]:
                return Rule.ROOM, f"room {room['room_id']} hosts {other['course_id']} in {slot['slot_id']}"
            shared = sorted(set(admitted[other["course_id"]]) & set(admitted[course["course_id"]]))
            if shared:
                return Rule.STUDENT, f"{shared[0]} attends {other['course_id']} in {slot['slot_id']}"
        for other in placed:
            if other["course_id"] == course["course_id"] and other["day"] == slot["day"]:
                return Rule.ONE_PER_DAY, f"{course['course_id']} already meets on {slot['day']}"
        return None

    def options(course: Row) -> list[tuple[Row, Row]]:
        return [(slot, room) for slot, room in product(slots, rooms) if refusal(course, slot, room) is None]

    def solve(index: int) -> bool | None:
        """True: every later session is placed; False: no placement works (a proof); None: the budget ran out."""
        nonlocal steps, backtracks, stopped_at
        if index == len(pending):
            return True
        course, number = pending[index]
        for slot, room in options(course):
            if steps == search_budget:
                stopped_at = (course, number)
                return None
            steps += 1
            placed.append(
                {
                    "course_id": course["course_id"],
                    "teacher_id": course["teacher_id"],
                    "number": number,
                    "slot_id": slot["slot_id"],
                    "day": slot["day"],
                    "room_id": room["room_id"],
                }
            )
            if all(options(later) for later, _ in pending[index + 1 :]):
                solved = solve(index + 1)
                if solved is not False:
                    return solved
            placed.pop()
            backtracks += 1
        return False

    proof = next((course["course_id"] for course, _ in pending if not options(course)), None)
    solved = False if proof is not None else solve(0)
    if solved is True:
        outcome, message = Outcome.SOLVED, f"every session is placed after {steps} steps and {backtracks} backtracks"
    elif solved is None and stopped_at is not None:
        outcome = Outcome.BUDGET_EXHAUSTED
        message = (
            f"the search stopped at {stopped_at[0]['course_id']} session {stopped_at[1]} after {steps} steps, "
            "the search_budget; no timetable was found, and this does not prove that none exists"
        )
    else:
        outcome = Outcome.INFEASIBLE
        message = (
            f"no timetable exists: {proof} has no free slot and room"
            if proof is not None
            else f"no timetable exists: every placement fails after {steps} steps"
        )
    entries: list[Row] = []
    decisions: list[Row] = []
    if outcome is Outcome.SOLVED:
        final, placed[:] = list(placed), []  # replay: a reason sees only the sessions placed before it
        by_course = {course["course_id"]: course for course in courses}
        for session in final:
            course = by_course[session["course_id"]]
            skipped = []
            for slot, room in product(slots, rooms):
                if (slot["slot_id"], room["room_id"]) == (session["slot_id"], session["room_id"]):
                    break
                rule, reason = refusal(course, slot, room) or (
                    Rule.UNDONE,
                    f"{slot['slot_id']} {room['room_id']} was tried and undone",
                )
                skipped.append({"place": f"{slot['slot_id']}/{room['room_id']}", "rule": rule.value, "reason": reason})
            session_id = f"{session['course_id']}/{session['number']}"
            entries.append({"session_id": session_id, **session})
            decisions.append({"session_id": session_id, "skipped": skipped})
            placed.append(session)
    return {
        "outcome": outcome.value,
        "search_complete": outcome in (Outcome.SOLVED, Outcome.INFEASIBLE),
        "message": message,
        "steps": steps,
        "backtracks": backtracks,
        "entries": entries,
        "decisions": decisions,
    }
