import random
from itertools import islice

match list:
    case islice:
        pass
ROWS = islice(random.random() for _ in range(3))  # W008
