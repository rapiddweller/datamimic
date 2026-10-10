# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from __future__ import annotations

import inspect
from collections.abc import Callable
from random import Random
from typing import TYPE_CHECKING

from datamimic_ce.engine.dsl.api import VariableStatement
from datamimic_ce.engine.runtime.contexts.context import Context, SetupContext
from datamimic_ce.engine.runtime.tasks.values.construction.entity_constructor import parse_constructor_string

if TYPE_CHECKING:
    from datamimic_ce.domains.api import BaseDomainService


def _constructor_params(cls: Callable[..., object]) -> frozenset[str]:
    """Names accepted by ``cls.__init__`` for optional runtime injection."""
    try:
        return frozenset(inspect.signature(cls).parameters)
    except (TypeError, ValueError):
        return frozenset()


def create_entity_generator(
    ctx: Context, entity_name: str, dataset: str, statement: VariableStatement
) -> BaseDomainService:
    from datamimic_ce.domains.api import DemographicConfig, get_entity_service_factory, spawn_rng

    entity_class_name, kwargs = parse_constructor_string(entity_name)
    kwargs.setdefault("dataset", dataset)
    demographic_context = ctx.root.demographic_context
    demo_cfg = None
    if any(
        value is not None
        for value in (statement.age_min, statement.age_max, statement.conditions_include, statement.conditions_exclude)
    ):
        includes = (
            frozenset(value.strip() for value in (statement.conditions_include or "").split(",") if value.strip())
            if statement.conditions_include is not None
            else None
        )
        excludes = (
            frozenset(value.strip() for value in (statement.conditions_exclude or "").split(",") if value.strip())
            if statement.conditions_exclude is not None
            else None
        )
        demo_cfg = DemographicConfig(
            age_min=statement.age_min,
            age_max=statement.age_max,
            conditions_include=includes,
            conditions_exclude=excludes,
        )
    rng_obj = Random(statement.rng_seed) if statement.rng_seed is not None else None
    if demo_cfg is None and demographic_context is not None and demographic_context.overrides is not None:
        demo_cfg = demographic_context.overrides
    if rng_obj is None and demographic_context is not None:
        rng_obj = spawn_rng(demographic_context.rng)
    if rng_obj is None:
        rng_obj = ctx.root.derive_seeded_rng()
    demographic_sampler = demographic_context.sampler if demographic_context is not None else None

    entity_cls = get_entity_service_factory(entity_class_name)
    if entity_cls is None:
        raise ValueError(f"Entity '{entity_name}' is not supported in the domain architecture.")

    accepted = _constructor_params(entity_cls)
    if demo_cfg is not None and "demographic_config" in accepted:
        kwargs.setdefault("demographic_config", demo_cfg)
    if demographic_sampler is not None and "demographic_sampler" in accepted:
        kwargs.setdefault("demographic_sampler", demographic_sampler)
    if rng_obj is not None and "rng" in accepted:
        kwargs["rng"] = rng_obj
    service = entity_cls(**kwargs)
    root = ctx.root
    if not isinstance(root, SetupContext):
        raise RuntimeError("Domain entity generation requires the setup context as root")
    service.set_identifier_registry(root.domain_identifier_registry)
    return service
