import random
from itertools import islice

islice: type = list
ROWS = islice(random.random() for _ in range(3))  # W008
