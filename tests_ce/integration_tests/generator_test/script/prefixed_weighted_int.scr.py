import json
import random

from datamimic_ce.domains.domain_core.base_literal_generator import BaseLiteralGenerator

DEFAULT_OFFSET_RULES = [
    {"threshold": 1, "min": 1, "max": 1},
]

NO_OFFSET = [
    {"threshold": 1, "min": 0, "max": 0},
]

SPARSE_ID_OFFSET_RULES = [
    {"threshold": 0.80, "min": 0, "max": 0},        # 80% (add increment only; no offset)
    {"threshold": 0.90, "min": 1, "max": 5},        # 10%
    {"threshold": 0.95, "min": 301, "max": 500},    #  5%
    {"threshold": 0.99, "min": 2501, "max": 2700},  #  4%
    {"threshold": 1, "min": 30001, "max": 30300}    #  1%
]

#---[ Global counters for persistent IDs ]--

customer_counter = 0

#---[ Id generation functions ]---

def customer_id():
    global customer_counter
    customer_counter += 1
    return f"C{customer_counter}"

#---[ Custom Generators ]---

class PrefixedWeightedInt(BaseLiteralGenerator):
    def __init__(self,
                 prefix = "",
                 increment = 1 ,
                 keep_counter = True,
                 offset_rules = None):

        self.counter = 0
        self.prefix = prefix
        self.keep_counter = bool(keep_counter)

        self.increment = int(increment) if isinstance(increment, (int, float, str)) else 1

        # JSON increment offset thesholding rules (if random value is less than
        # or equal to a specified threshold, that min max pair is used to generate offset)
        default_rules = DEFAULT_OFFSET_RULES

        if isinstance(offset_rules, str):
            # Parse JSON string
            self.offset_rules = json.loads(offset_rules)
        else:
            self.offset_rules = offset_rules or default_rules

    def generate(self) -> str:
        r = random.random()
        offset = 0
        for rule in self.offset_rules:
            if r <= rule["threshold"]:
                offset = random.randint(rule["min"], rule["max"])
                break

        # calculate our increment
        our_increment = self.increment + offset

        # default to return only this increment
        our_return_val = our_increment

        # If keeping a continuous counter, update it
        if self.keep_counter:
            assert our_increment > 0, "If keeping a counter, increment must be positive and non-zero"
            self.counter += our_increment
            # set our return to our newly aggregated counter
            our_return_val = self.counter

        return f"{self.prefix}{our_return_val}"
