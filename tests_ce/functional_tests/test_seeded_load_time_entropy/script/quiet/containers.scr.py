import random

# A container only holds the generator.
LISTED = [(random.random() for _ in range(3))]
TUPLED = ((random.random() for _ in range(3)), 1)
SETTED = {(random.random() for _ in range(3))}
MAPPED = {"a": (random.random() for _ in range(3))}
