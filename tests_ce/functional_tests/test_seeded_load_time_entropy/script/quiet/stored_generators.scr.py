import random

POOL = (random.random() for _ in range(3))
WRAPPED = iter(random.random() for _ in range(3))
PAIRED = zip((random.random() for _ in range(3)), (random.random() for _ in range(3)))
NESTED = enumerate(map(abs, (random.random() for _ in range(3))))
(random.random() for _ in range(3))
