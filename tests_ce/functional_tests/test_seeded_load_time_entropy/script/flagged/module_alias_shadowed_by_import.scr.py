import random
import sys
from types import SimpleNamespace

# An eager stand-in module: its islice consumes the generator.
sys.modules["w008_eager_tools"] = SimpleNamespace(islice=lambda values, count: list(values)[:count])
import itertools as it
import w008_eager_tools as it

HEAD = it.islice((random.random() for _ in range(3)), 2)  # W008
del sys.modules["w008_eager_tools"]
