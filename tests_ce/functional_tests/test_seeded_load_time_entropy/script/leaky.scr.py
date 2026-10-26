import random

BOOT = random.randint(1, 10)


def token(x, salt=random.random()):
    import uuid
    return x + salt + BOOT + len(uuid.uuid4().hex)
