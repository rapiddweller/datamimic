import random


# A call at load consumes the default before the seeded names replace `random`: the replay breaks.
def first(values=(random.random() for _ in range(3))):  # W008
    return next(values)


BOOT = first()
