import random


# The element runs when the function consumes it, with the seeded names.
def first(values=(random.random() for _ in range(3))):
    return next(values)


def first_keyword(*, values=(random.random() for _ in range(3))):
    return next(values)


FIRST = lambda values=(random.random() for _ in range(3)): next(values)
