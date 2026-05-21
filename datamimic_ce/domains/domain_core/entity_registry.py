# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Registry for domain entity services.

Discovers ``BaseDomainService`` subclasses across ``datamimic_ce.domains.*``
so the DSL can resolve ``entity="Person"`` to a service class without a
hand-maintained mapping. Each entity also carries its declared attribute
specs so the schema-consistency gate can check them.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from collections.abc import Iterable
from dataclasses import dataclass
from types import ModuleType

from datamimic_ce.domains.domain_core.attribute_catalog import FieldSpec
from datamimic_ce.domains.domain_core.base_domain_service import BaseDomainService

_DOMAINS_PREFIX = "datamimic_ce.domains."


@dataclass(frozen=True)
class EntitySpec:
    entity: str
    service_cls: type[BaseDomainService]
    module: str
    attributes: tuple[FieldSpec, ...]


_ENTITY_REGISTRY: dict[str, EntitySpec] = {}
_CLASS_TO_SPEC: dict[type[BaseDomainService], EntitySpec] = {}
_LOADED: bool = False


def _ensure_loaded() -> None:
    global _LOADED
    if not _LOADED:
        auto_register_entities()
        _LOADED = True


def auto_register_entities() -> None:
    """Discover BaseDomainService subclasses across datamimic_ce.domains.* services."""
    import datamimic_ce.domains as domains_pkg

    for module in _iter_service_modules(domains_pkg):
        for _, cls in inspect.getmembers(module, inspect.isclass):
            if not issubclass(cls, BaseDomainService) or cls is BaseDomainService:
                continue
            # Only register a class in the module that defines it (skip re-exports).
            if cls.__module__ != module.__name__:
                continue
            _register_service_class(cls)


def _iter_service_modules(root_pkg: ModuleType) -> Iterable[ModuleType]:
    """Yield modules under datamimic_ce.domains.* whose dotted name includes '.services'."""
    if not hasattr(root_pkg, "__path__"):
        return
    for _, name, _ in pkgutil.walk_packages(root_pkg.__path__, root_pkg.__name__ + "."):
        if ".services" not in name:
            continue
        yield importlib.import_module(name)


def _entity_name_for(cls: type[BaseDomainService]) -> str:
    name = cls.__name__
    return name[:-7] if name.endswith("Service") else name


def _register_service_class(cls: type[BaseDomainService]) -> None:
    if cls in _CLASS_TO_SPEC:
        return
    entity_name = _entity_name_for(cls)
    spec = EntitySpec(
        entity=entity_name,
        service_cls=cls,
        module=cls.__module__,
        attributes=cls.attribute_specs(),
    )
    _CLASS_TO_SPEC[cls] = spec
    for alias in _aliases_for(cls, entity_name):
        _ENTITY_REGISTRY.setdefault(alias, spec)


def _aliases_for(cls: type[BaseDomainService], entity_name: str) -> set[str]:
    service_name = cls.__name__
    module = cls.__module__
    names = {entity_name, service_name, f"{module}.{service_name}"}
    if module.startswith(_DOMAINS_PREFIX):
        names.add(f"{module[len(_DOMAINS_PREFIX):]}.{service_name}")
    return {name for name in names if name}


def list_entity_specs() -> tuple[EntitySpec, ...]:
    _ensure_loaded()
    seen: set[type[BaseDomainService]] = set()
    ordered: list[EntitySpec] = []
    for spec in _ENTITY_REGISTRY.values():
        if spec.service_cls in seen:
            continue
        seen.add(spec.service_cls)
        ordered.append(spec)
    return tuple(ordered)


def get_entity_spec(name: str) -> EntitySpec | None:
    _ensure_loaded()
    spec = _ENTITY_REGISTRY.get(name)
    if spec is not None:
        return spec
    if name.startswith(_DOMAINS_PREFIX):
        spec = _ENTITY_REGISTRY.get(name[len(_DOMAINS_PREFIX):])
        if spec is not None:
            return spec
    if "." in name:
        spec = _ENTITY_REGISTRY.get(name.split(".")[-1])
    return spec


def get_entity_service_class(name: str) -> type[BaseDomainService] | None:
    spec = get_entity_spec(name)
    return spec.service_cls if spec else None
