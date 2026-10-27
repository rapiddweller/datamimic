import random
from contextlib import nullcontext
from itertools import islice

with nullcontext(list) as islice:
    pass
ROWS = islice(random.random() for _ in range(3))  # W008
