"""Helpers using the import forms found in project scripts; under rngSeed they must replay."""

import datetime
import random
import random as rnd
import uuid
from datetime import datetime as Datetime
from datetime import timedelta
from random import Random


def helper_draw() -> int:
    return random.randint(1, 10**9)


def helper_own_random() -> int:
    return Random().randint(1, 10**9)


def helper_alias_draw() -> int:
    return rnd.randint(1, 10**9)


def helper_uuid() -> str:
    return str(uuid.uuid4())


def helper_now() -> str:
    return datetime.datetime.now().isoformat()


def helper_due_date(days: int) -> str:
    return (Datetime.now() + timedelta(days=days)).date().isoformat()


def helper_type_checks() -> str:
    """Type checks against imported classes must not change under a seed."""
    return f"{isinstance(Datetime.now(), Datetime)}/{isinstance(Random(1), Random)}"
