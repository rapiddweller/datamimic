import random

VALUES = [*(y for x in range(1) for y in (random.random() for _ in range(2)))]  # W008
