"""Scripted Random doubles shared by the generator behavior tests."""

from random import Random


class ScriptedIntegerRandom(Random):
    def __init__(self, values: list[int]) -> None:
        self.values = iter(values)
        self.bounds: list[tuple[int, int]] = []
        super().__init__(0)

    def randint(self, a: int, b: int) -> int:
        self.bounds.append((a, b))
        return next(self.values)


class FixedBitsRandom(Random):
    def __init__(self) -> None:
        super().__init__(1)
        self.bit_requests: list[int] = []
        self.fail_next_uuid = False

    def getrandbits(self, k: int) -> int:
        self.bit_requests.append(k)
        if k == 128 and self.fail_next_uuid:
            self.fail_next_uuid = False
            raise RuntimeError("scripted UUID draw failure")
        return 0


class ScriptedRandom(Random):
    def __init__(self, values: list[float]):
        super().__init__(0)
        self.values = iter(values)
        self.draw_count = 0

    def random(self) -> float:
        self.draw_count += 1
        return next(self.values)
