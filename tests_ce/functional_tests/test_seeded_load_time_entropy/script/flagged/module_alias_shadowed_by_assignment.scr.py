import itertools as it
import random
from types import SimpleNamespace

it = SimpleNamespace(islice=lambda values, count: list(values)[:count])
HEAD = it.islice((random.random() for _ in range(3)), 2)  # W008
