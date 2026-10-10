# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

class GlobalIncrementRegistry:
    def __init__(self) -> None:
        self.counters: dict[str, int] = {}

    def register(self, key: str, start: int = 1) -> None:
        self.counters[key] = start

    def next(self, key: str) -> int:
        value = self.counters[key]
        self.counters[key] += 1
        return value

    def reset(self) -> None:
        self.counters.clear()
