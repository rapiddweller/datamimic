import itertools as it
import random

PICKS = it.combinations((random.random() for _ in range(3)), 2)  # W008
