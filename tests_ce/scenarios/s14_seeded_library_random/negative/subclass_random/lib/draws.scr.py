from random import Random, randint, triangular


# A subclass made while the library loads is not the seeded Random, so its draws differ per run.
class LocalRandom(Random):
    pass


def spread():
    return round(triangular(0, 10, 3), 6)


def shape():
    return LocalRandom().random()


def dice():
    return randint(1, 6)


def fresh():
    return 1


def reseed():
    return 1


def restored():
    return True
