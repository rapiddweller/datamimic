import random


def islice(values, count):
    return list(values)[:count]


HEAD = islice((random.random() for _ in range(3)), 2)  # W008
