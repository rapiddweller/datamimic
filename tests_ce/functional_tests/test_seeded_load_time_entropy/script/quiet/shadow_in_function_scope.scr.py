import random
from itertools import islice


def helper():
    # A local name: the module-level islice stays the lazy import.
    islice = list
    return islice(())


HEAD = islice((random.random() for _ in range(3)), 2)
