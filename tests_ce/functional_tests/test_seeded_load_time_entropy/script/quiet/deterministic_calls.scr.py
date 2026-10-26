import math
import time
import uuid
from datetime import datetime

FIXED = datetime(2020, 1, 1)
NAME = uuid.uuid5(uuid.NAMESPACE_DNS, "a")
START = time.perf_counter()
HALF = math.floor(1.5)
