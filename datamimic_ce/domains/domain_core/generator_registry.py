# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Registry for DSL-exposable literal generators.

Discovers generator classes under ``datamimic_ce.domains.*.literal_generators``
so the DSL can resolve ``generator="StringGenerator"`` (and the surrounding
``evaluate_python_expression`` namespace) without a hand-maintained dict.

Discovery is location- and name-based: any class **defined in** a
``*.literal_generators`` module whose name ends with ``Generator``. Entity
generators (under ``*/generators/``) are intentionally excluded — those are
reachable as DSL entities, not as ``generator=`` targets.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from collections.abc import Iterable
from types import ModuleType

_LITERAL_PKG_MARKER = ".literal_generators"

_REGISTRY: dict[str, type] = {}
_LOADED: bool = False


def _ensure_loaded() -> None:
    global _LOADED
    if not _LOADED:
        auto_register_generators()
        _LOADED = True


def auto_register_generators() -> None:
    """Discover generator classes across datamimic_ce.domains.*.literal_generators."""
    import datamimic_ce.domains as domains_pkg

    for module in _iter_literal_generator_modules(domains_pkg):
        for name, cls in inspect.getmembers(module, inspect.isclass):
            if not name.endswith("Generator"):
                continue
            # Only the class defined in this module (skip imported re-exports).
            if cls.__module__ != module.__name__:
                continue
            _REGISTRY.setdefault(name, cls)


def _iter_literal_generator_modules(root_pkg: ModuleType) -> Iterable[ModuleType]:
    # `literal_generators` is a namespace package (no __init__) which
    # pkgutil.walk_packages skips during recursion, so resolve it explicitly
    # per domain: import "<domain>.literal_generators" and iterate its modules.
    if not hasattr(root_pkg, "__path__"):
        return
    for _, domain_name, is_pkg in pkgutil.iter_modules(root_pkg.__path__, root_pkg.__name__ + "."):
        if not is_pkg:
            continue
        try:
            lit_pkg = importlib.import_module(f"{domain_name}{_LITERAL_PKG_MARKER}")
        except ModuleNotFoundError:
            continue
        for _, mod_name, _ in pkgutil.iter_modules(lit_pkg.__path__, lit_pkg.__name__ + "."):
            yield importlib.import_module(mod_name)


def get_generator_class(name: str) -> type | None:
    _ensure_loaded()
    return _REGISTRY.get(name)


def list_generator_names() -> list[str]:
    _ensure_loaded()
    return sorted(_REGISTRY.keys())


def generator_namespace() -> dict[str, type]:
    """Return a name->class map for use as an eval namespace in the DSL engine."""
    _ensure_loaded()
    return dict(_REGISTRY)
