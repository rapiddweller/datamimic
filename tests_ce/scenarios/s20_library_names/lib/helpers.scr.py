import random
from datetime import datetime as Datetime
from random import randint


# Replaces the engine's hex on purpose: a name the library defines wins over the engine's name.
def hex(value):
    return format(value, "04x")


def stamp(day):
    return Datetime(2026, 3, day).date().isoformat()


def dice():
    return randint(1, 6)


def coin():
    return random.choice(["heads", "tails"])


# A class the project defines: Build shows its message, as it never shows the message of a builtin (#707).
class Infeasible(Exception):
    pass


def infeasible(day):
    raise Infeasible("no feasible assignment")
