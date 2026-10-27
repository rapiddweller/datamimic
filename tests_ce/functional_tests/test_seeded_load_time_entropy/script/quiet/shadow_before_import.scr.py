import random

islice = list
# The later import wins: islice is lazy again.
from itertools import islice

HEAD = islice((random.random() for _ in range(3)), 2)
