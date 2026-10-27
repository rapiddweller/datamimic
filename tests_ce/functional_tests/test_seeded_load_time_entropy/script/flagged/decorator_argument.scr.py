import random


def tagged(values):
    return lambda function: function


@tagged(random.random() for _ in range(3))  # W008
def task():
    return None
