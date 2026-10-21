"""Candidate selection for a staffing model (#332): a library the bounded run may load."""

import random

LOADS: list[int] = []
LOADS.append(1)  # runs once per load; the model shows len(LOADS)


def select_person(candidates: list[tuple[int, bool]]) -> int:
    for person_id, eligible in candidates:
        if eligible:
            return person_id
    raise ValueError("No eligible candidate")


def draw() -> int:
    return random.randint(1, 10**9)
