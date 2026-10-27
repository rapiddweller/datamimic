import itertools
import itertools as it
import random
from itertools import chain as joined
from itertools import islice

# Each wrapper only holds the generator; it runs later, when something consumes the wrapper.
HEAD = itertools.islice((random.random() for _ in range(3)), 2)
HEAD_IMPORTED = islice((random.random() for _ in range(3)), 2)
JOINED = joined((random.random() for _ in range(3)), ())
CHAINED = it.chain((random.random() for _ in range(3)), ())
CYCLED = itertools.cycle(random.random() for _ in range(3))
COPIES = itertools.tee(random.random() for _ in range(3))
WHILE_SMALL = itertools.takewhile(bool, (random.random() for _ in range(3)))
AFTER_SMALL = itertools.dropwhile(bool, (random.random() for _ in range(3)))
TOTALS = itertools.accumulate(random.random() for _ in range(3))
KEPT = itertools.compress((random.random() for _ in range(3)), (1, 0, 1))
GROUPS = itertools.groupby(random.random() for _ in range(3))
STARRED = itertools.starmap(max, ((random.random(), 1) for _ in range(3)))
LONGEST = itertools.zip_longest((random.random() for _ in range(3)), ())
FALSE = itertools.filterfalse(bool, (random.random() for _ in range(3)))
PAIRS = itertools.pairwise(random.random() for _ in range(3))
