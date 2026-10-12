# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.domains.api import BaseLiteralGenerator
from datamimic_ce.engine.runtime.contexts.context import Context
from datamimic_ce.engine.runtime.storage.global_increment import GlobalIncrementRegistry


class GlobalIncrementGenerator(BaseLiteralGenerator):
    """Global, monotonic increment scoped to one root context and qualified key."""

    def __init__(self, qualified_key: str, context: Context) -> None:
        self.qualified_key = qualified_key
        registry = context.root.global_increment_registry
        if registry is None:
            registry = GlobalIncrementRegistry()
            context.root.global_increment_registry = registry
        self._registry = registry
        if qualified_key not in self._registry.counters:
            self._registry.register(qualified_key)

    def generate(self) -> int:
        return self._registry.next(self.qualified_key)
