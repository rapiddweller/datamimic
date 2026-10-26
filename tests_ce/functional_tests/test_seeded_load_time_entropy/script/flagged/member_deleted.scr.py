import random
from itertools import islice

# After del the scan cannot follow the name: globals() rebinds it out of sight.
del islice
globals()["islice"] = list
ROWS = islice(random.random() for _ in range(3))  # W008
