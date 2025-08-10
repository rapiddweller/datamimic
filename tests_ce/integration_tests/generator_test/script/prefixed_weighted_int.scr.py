import json
import random

from datamimic_ce.domain_core.base_literal_generator import BaseLiteralGenerator

random.seed(1)

DEFAULT_OFFSET_RULES = [
    {"threshold": 1, "min": 1, "max": 1},
]

NO_OFFSET = [
    {"threshold": 1, "min": 0, "max": 0},
]

SPARSE_ID_OFFSET_RULES = [
    {"threshold": 0.80, "min": 0, "max": 0},
    {"threshold": 0.90, "min": 1, "max": 5},
    {"threshold": 0.95, "min": 301, "max": 500},
    {"threshold": 0.99, "min": 2501, "max": 2700},
    {"threshold": 1, "min": 30001, "max": 30300},
]


class PrefixedWeightedInt(BaseLiteralGenerator):
    def __init__(self, prefix="", increment=1, keep_counter=True, offset_rules=None):
        self.counter = 0
        self.prefix = prefix
        self.keep_counter = bool(keep_counter)
        self.increment = int(increment) if isinstance(increment, int | float | str) else 1
        if isinstance(offset_rules, str):
            self.offset_rules = json.loads(offset_rules)
        else:
            self.offset_rules = offset_rules or DEFAULT_OFFSET_RULES

    def generate(self) -> str:  # pragma: no cover - simple helper
        r = random.random()
        offset = 0
        for rule in self.offset_rules:
            if r <= rule["threshold"]:
                offset = random.randint(rule["min"], rule["max"])
                break
        our_increment = self.increment + offset
        result = our_increment
        if self.keep_counter:
            assert our_increment > 0, "If keeping a counter, increment must be positive and non-zero"
            self.counter += our_increment
            result = self.counter
        return f"{self.prefix}{result}"
