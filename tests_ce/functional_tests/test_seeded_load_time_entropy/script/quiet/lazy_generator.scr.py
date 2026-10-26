import random

POOL = (random.random() for _ in range(3))
PICKS = map(abs, (random.random() for _ in range(3)))
