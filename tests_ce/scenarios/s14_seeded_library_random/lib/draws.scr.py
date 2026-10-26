import random
from random import (
    Random,
    betavariate,
    expovariate,
    gammavariate,
    getstate,
    lognormvariate,
    normalvariate,
    paretovariate,
    randint,
    setstate,
    triangular,
    vonmisesvariate,
)
from random import weibullvariate as weibull


def spread():
    return round(triangular(0, 10, 3), 6)


def shape():
    values = (
        betavariate(2, 5),
        expovariate(1.5),
        gammavariate(2, 2),
        lognormvariate(0, 0.5),
        normalvariate(0, 1),
        paretovariate(3),
        vonmisesvariate(0, 4),
        weibull(1, 1.5),
    )
    return round(sum(values), 6)


def dice():
    return randint(1, 6)


def fresh():
    return Random().randint(1, 10**9)


def reseed():
    random.seed()
    return random.randint(1, 10**9)


def restored():
    state = getstate()
    first = random.random()
    setstate(state)
    return random.random() == first
