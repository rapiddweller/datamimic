import random
from itertools import islice


# The local def replaces the imported lazy islice and consumes the generator.
def islice(values, count):
    return list(values)[:count]


HEAD = islice((random.random() for _ in range(3)), 2)  # W008
