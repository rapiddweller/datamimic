import itertools as it
import random


# The class replaces the itertools alias and its islice consumes the generator.
class it:
    @staticmethod
    def islice(values, count):
        return list(values)[:count]


HEAD = it.islice((random.random() for _ in range(3)), 2)  # W008
