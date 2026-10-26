import random
from itertools import islice

try:
    raise ValueError
except ValueError as islice:
    pass
# The except name was the last binding and is gone: globals() rebinds it out of sight.
globals()["islice"] = list
ROWS = islice(random.random() for _ in range(3))  # W008
