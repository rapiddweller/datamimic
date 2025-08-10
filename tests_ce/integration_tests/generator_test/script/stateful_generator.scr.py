from datamimic_ce.domain_core.base_literal_generator import BaseLiteralGenerator

class StatefulIncrementGenerator(BaseLiteralGenerator):
    def __init__(self):
        self._value = 0

    def generate(self) -> int:
        self._value += 1
        return self._value
