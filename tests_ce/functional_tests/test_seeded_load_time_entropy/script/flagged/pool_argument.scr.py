import random


class Pool:
    def __init__(self, values):
        self.values = list(values)


POOL = Pool(random.random() for _ in range(3))  # W008
