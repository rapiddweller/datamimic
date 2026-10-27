import random
from itertools import islice

for islice in (list,):
    pass
ROWS = islice(random.random() for _ in range(3))  # W008
