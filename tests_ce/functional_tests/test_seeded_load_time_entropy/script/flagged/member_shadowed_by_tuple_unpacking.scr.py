import random
from itertools import islice

islice, _ = list, None
ROWS = islice(random.random() for _ in range(3))  # W008
