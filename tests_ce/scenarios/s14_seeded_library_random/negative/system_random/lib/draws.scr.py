from random import SystemRandom, randint, triangular


def spread():
    return round(triangular(0, 10, 3), 6)


def shape():
    return round(SystemRandom().random(), 6)


def dice():
    return randint(1, 6)


def fresh():
    return 1


def reseed():
    return 1


def restored():
    return True
