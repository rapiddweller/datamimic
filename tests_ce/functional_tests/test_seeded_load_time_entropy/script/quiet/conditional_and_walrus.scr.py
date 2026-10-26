import random

FLAG = True
# The generator is stored or tested for truth, not run.
CHOSEN = (random.random() for _ in range(3)) if FLAG else ()
if (STORED := (random.random() for _ in range(3))):
    pass
while (LOOPED := (random.random() for _ in range(3))):
    break
