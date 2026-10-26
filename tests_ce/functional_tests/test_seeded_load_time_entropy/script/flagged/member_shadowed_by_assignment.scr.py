import random
from itertools import islice

# The assignment replaces the lazy islice: list consumes the generator.
islice = list
ROWS = islice(random.random() for _ in range(3))  # W008
