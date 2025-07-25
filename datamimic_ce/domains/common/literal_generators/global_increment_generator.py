# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.domain_core.base_literal_generator import BaseLiteralGenerator


class GlobalIncrementRegistry:
    def __init__(self):
        self.counters = {}

    def register(self, key, start=1):
        self.counters[key] = start

    def next(self, key):
        value = self.counters[key]
        self.counters[key] += 1
        return value

    def reset(self):
        self.counters.clear()


class GlobalIncrementGenerator(BaseLiteralGenerator):
    def __init__(self, qualified_key, context):
        self.qualified_key = qualified_key
        if not hasattr(context.root, "_global_increment_registry"):
            context.root._global_increment_registry = GlobalIncrementRegistry()
        self._registry = context.root._global_increment_registry
        if qualified_key not in self._registry.counters:
            self._registry.register(qualified_key)

    def generate(self):
        return self._registry.next(self.qualified_key)
