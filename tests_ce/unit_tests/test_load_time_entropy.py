# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""The static scan for entropy a script draws while it loads (#359); the model-level behavior is pinned by
functional_tests/test_seeded_load_time_entropy."""

import pytest

from datamimic_ce.engine.runtime.scripting.expression_globals import LoadTimeDraw, load_time_entropy


@pytest.mark.parametrize(
    "source",
    [
        "import random\nX = random.randint(1, 2)",
        "import random as r\nX = r.random()",
        "from random import randint\nX = randint(1, 2)",
        "from random import randint as pick\nX = pick(1, 2)",
        "from datetime import datetime\nX = datetime.now()",
        "import datetime\nX = datetime.datetime.utcnow()",
        "import uuid\nX = uuid.uuid4()",
        "import os\nX = os.urandom(4)",
        "import random\nX = random.Random()",
        "import random\ndef f(x=random.random()):\n    return x",
        "import random\nclass C:\n    seed = random.random()",
        "import random\n@random.choice([1, 2])\ndef f():\n    pass",
        "import random\nX = random.Random(None)",
        "import random\nrandom.seed(None)",
        "import random\nrandom.seed(version=2)",
        "import random\nV = list(x for x in range(random.randint(1, 3)))",
        "import random\nTOKEN = ''.join(random.choice('abc') for _ in range(12))",
        "import random\nV = sum(random.random() for _ in range(3))",
        "import random\nV = list(x for x in range(3) if random.random() > 0.5)",
    ],
)
def test_a_draw_that_runs_while_the_module_loads_is_found(source: str) -> None:
    assert [finding.draw for finding in load_time_entropy(source)] == [LoadTimeDraw.MODULE_LEVEL_CALL]


@pytest.mark.parametrize(
    "source",
    [
        "import random\ndef f():\n    return random.randint(1, 2)",
        "import random\nRNG = random.Random(7)",
        "import random\nRNG = random.Random(x=7)",
        "import random\nrandom.seed(a=7, version=2)",
        "import random\ndef f(x: random.random()):\n    pass",  # annotations are postponed by the runtime
        "import random\ndef f() -> random.random():\n    pass",
        "import random\nV = iter(random.random() for _ in range(3))",
        "import random\nV = enumerate(random.random() for _ in range(3))",
        "import random\nV = map(abs, (random.random() for _ in range(3)))",
        "import random\nV = (random.random() for _ in range(3))",
        "import random\nV = (x for x in range(3) if random.random() > 0.5)",
        "import random\nrandom.seed(7)",
        "from random import Random\nRNG = Random(7)",
        "import time\nT = time.perf_counter()",
        "import secrets\nT = secrets.token_hex(4)",
        "def f():\n    from datetime import timedelta\n    return timedelta(1)",
        "def f():\n    import time\n    time.sleep(0)\n    import uuid\n    return uuid.UUID(int=1)",
        "import random\nF = lambda: random.random()",
        "import datetime\nX = datetime.datetime(2020, 1, 1)",
        "import uuid\nX = uuid.uuid5(uuid.NAMESPACE_DNS, 'a')",
        "import math\nX = math.floor(1.5)",
        "X = unknown.random()",
        "def broken(:",
    ],
)
def test_deterministic_code_and_draws_inside_bodies_are_not_reported(source: str) -> None:
    assert load_time_entropy(source) == ()


def test_an_alias_reused_by_a_helper_does_not_hide_the_module_level_binding():
    source = "import random as r\nX = r.random()\ndef helper():\n    import os as r\n    return r.getpid()\n"
    assert [finding.line for finding in load_time_entropy(source)] == [2]


def test_a_helper_alias_does_not_leak_into_the_module_scope():
    source = "def helper():\n    import random as r\n    return r.random()\nX = r.random()\n"
    assert [finding.draw for finding in load_time_entropy(source)] == [LoadTimeDraw.IMPORT_IN_BODY]  # not line 4


def test_an_entropy_import_inside_a_body_is_found_with_its_line() -> None:
    findings = load_time_entropy(
        "def f():\n    import random\n    return random.random()\n\n"
        "class C:\n    from uuid import uuid4\n    x = uuid4()\n"
    )
    assert [(finding.draw, finding.line) for finding in findings] == [
        (LoadTimeDraw.IMPORT_IN_BODY, 2),
        (LoadTimeDraw.IMPORT_IN_BODY, 6),
        (LoadTimeDraw.MODULE_LEVEL_CALL, 7),  # a class body runs while the module loads
    ]
