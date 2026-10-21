"""Helpers using the import forms found in project scripts; under rngSeed they must replay."""

import datetime
import random
import random as rnd
import uuid
from datetime import datetime as Datetime
from datetime import timedelta
from random import Random, randint, sample


def helper_draw() -> int:
    return random.randint(1, 10**9)


def helper_own_random() -> str:
    return f"{Random().randint(1, 10**9)}/{random.Random(None).randint(1, 10**9)}"


def helper_alias_draw() -> int:
    return rnd.randint(1, 10**9)


def helper_direct_import_draw() -> str:
    return f"{randint(1, 10**9)}/{sample(range(100), 3)}"


def helper_uuid() -> str:
    return str(uuid.uuid4())


def helper_now() -> str:
    return datetime.datetime.now().isoformat()


def helper_due_date(days: int) -> str:
    return (Datetime.now() + timedelta(days=days)).date().isoformat()


def helper_type_checks() -> str:
    """Type checks against imported classes must not change under a seed."""
    checks = (
        isinstance(Datetime.now(), Datetime),
        isinstance(random.Random(1), Random),
        isinstance(Random(), random.Random),
    )
    return "/".join(str(check) for check in checks)


def helper_keyed_draw(key: int) -> int:
    """Reseeding the module with a key cannot hold under rngSeed; seeded_reject_script_keyed_seed.xml calls it."""
    random.seed(key)
    return random.randint(1, 10**6)
