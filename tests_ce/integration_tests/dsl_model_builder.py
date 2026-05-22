# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Registry-driven builder for the full seeded-replay DSL model.

Renders one ``<generate>`` block per registered entity (all entities + a
representative scalar from every attribute and reliably-reachable sub-structure),
so a single function describes the complete model. Seeding is parameterised so the
same full model can be emitted for each determinism scenario:

* ``build_all_entities_seeded_xml()`` (default: per-variable ``rngSeed``) is the
  committed ``all_entities_seeded.xml`` replayed by ``test_determinism_dsl``.
* ``setup_seed`` / ``variable_seed`` toggle ``<setup rngSeed>`` and the per-variable
  ``rngSeed`` for the setup-seed / override / no-seed scenarios.
"""

from __future__ import annotations

import re
from datetime import date, datetime

from datamimic_ce.domains.domain_core.entity_registry import EntitySpec, list_entity_specs

SEED = 42
COUNT = 3
KEYS_PER_ENTITY = 3
_SCALAR_TYPES = (str, int, float, bool, datetime, date)


def _is_scalar(value: object) -> bool:
    return value is not None and isinstance(value, _SCALAR_TYPES)


def _is_entity_obj(value: object) -> bool:
    """A nested model/record exposed as an object (reached via ``.attr``)."""
    return not isinstance(value, dict) and hasattr(value, "to_dict")


def _scalar_leaf_fields(spec: EntitySpec) -> list:
    """Leaf (non-grouped) fields with a scalar python type, in declared order."""
    return [
        f
        for f in spec.attributes
        if not f.children and isinstance(f.py_type, type) and issubclass(f.py_type, _SCALAR_TYPES)
    ]


def _scalar_subkeys(obj: object) -> list[str]:
    """Names of scalar leaves of a nested record (entity object or plain dict)."""
    mapping = obj.to_dict() if _is_entity_obj(obj) else obj
    return [k for k, v in mapping.items() if _is_scalar(v)]


def _slug(name: str) -> str:
    """A key-name-safe slug for a sub-field (data dict keys may contain spaces)."""
    return re.sub(r"\W", "_", name)


def _first(items: list[str]) -> str | None:
    return items[0] if items else None


def _nested_path(field: str, value: object) -> tuple[str, str] | None:
    """The ``(name, script_expr)`` reaching one scalar inside a nested field.

    Reflects how a DSL script navigates a sub-structure: sub-objects via attribute
    access (``e.address.street``), plain data dicts via item access
    (``e.office_hours['Monday']``), and lists via ``[0]``. Returns ``None`` for a
    field with no reachable scalar (e.g. an empty list).
    """
    if _is_entity_obj(value):
        s = _first(_scalar_subkeys(value))
        return (f"{field}_{s}", f"e.{field}.{s}") if s else None
    if isinstance(value, dict):
        s = _first(_scalar_subkeys(value))
        return (f"{field}_{_slug(s)}", f"e.{field}[{s!r}]") if s else None
    if isinstance(value, list) and value:
        item = value[0]
        if _is_entity_obj(item):
            s = _first(_scalar_subkeys(item))
            return (f"{field}_0_{s}", f"e.{field}[0].{s}") if s else None
        if isinstance(item, dict):
            s = _first(_scalar_subkeys(item))
            return (f"{field}_0_{_slug(s)}", f"e.{field}[0][{s!r}]") if s else None
        if _is_scalar(item):
            return f"{field}_0", f"e.{field}[0]"
    return None


def _failing_keys(spec: EntitySpec, keys: list[tuple[str, str]]) -> set[str]:
    """Names of keys that raise when accessed exactly as the DSL block would.

    Replays the DSL's access pattern faithfully: a single seeded service shared
    across ``COUNT`` records (the records share one RNG, so generated values are
    sensitive to access order), evaluating every key script per record in the
    same order they are emitted. A name is reported failing if it errors on any
    record (e.g. a missing dict key or an empty list index).
    """
    from random import Random

    service = spec.service_cls(rng=Random(SEED))
    failing: set[str] = set()
    for _ in range(COUNT):
        rec = service.generate()
        for name, expr in keys:
            try:
                eval(expr, {"__builtins__": {}}, {"e": rec})  # noqa: S307 - test-only, fixed inputs
            except Exception:
                failing.add(name)
    return failing


def _entity_keys(spec: EntitySpec) -> list[tuple[str, str]]:
    """``(name, script)`` keys for one entity: scalar leaves + nested sub-structure.

    Nested candidates (one scalar reached through each sub-object / data dict /
    list) are pruned to those that survive a faithful replay of the DSL access
    pattern. Because the records share one RNG and fields are lazy, removing a key
    changes what later keys see — so prune to a fixpoint where every emitted key
    resolves for every record, exactly as it will at runtime.
    """
    from random import Random

    scalars = [(f.name, f"e.{f.name}") for f in _scalar_leaf_fields(spec)[:KEYS_PER_ENTITY]]
    if not scalars:
        raise ValueError(f"Entity '{spec.entity}' exposes no scalar field to seed the determinism model with.")

    sample = spec.service_cls(rng=Random(SEED)).generate()
    nested: list[tuple[str, str]] = []
    for field, value in sample.to_dict().items():
        if not isinstance(value, dict | list):
            continue
        prop = getattr(sample, field, value)  # scripts reach the property, not the serialised value
        candidate = _nested_path(field, prop)
        if candidate is not None:
            nested.append(candidate)

    keys = scalars + nested
    while failing := _failing_keys(spec, keys):
        keys = [k for k in keys if k[0] not in failing]
    return keys


def build_all_entities_seeded_xml(*, setup_seed: int | None = None, variable_seed: int | None = SEED) -> str:
    """Render the full seeded-replay DSL model from the entity registry.

    One ``<generate>`` block per registered entity (sorted by name), each exposing
    the first few scalar fields plus one scalar reached *through* every reliably
    accessible sub-structure. Seeding is parameterised:

    * ``setup_seed`` — emit ``<setup rngSeed="…">`` (model-wide root) when set.
    * ``variable_seed`` — emit ``rngSeed="…"`` on each ``<variable>`` when set.

    The default (``setup_seed=None``, ``variable_seed=SEED``) is the committed
    ``all_entities_seeded.xml``.
    """
    setup_attrs = 'multiprocessing="0"'
    if setup_seed is not None:
        setup_attrs += f' rngSeed="{setup_seed}"'
    lines = [
        f"<setup {setup_attrs}>",
        "    <!-- AUTO-GENERATED from the entity registry by build_all_entities_seeded_xml(). -->",
        "    <!-- Do not edit by hand; regenerate via test_determinism_dsl.py (see module docstring). -->",
    ]
    for spec in sorted(list_entity_specs(), key=lambda s: s.entity):
        var_attrs = f'name="e" entity="{spec.entity}" dataset="US"'
        if variable_seed is not None:
            var_attrs += f' rngSeed="{variable_seed}"'
        lines.append(f'    <generate name="{spec.entity.lower()}" count="{COUNT}" target="">')
        lines.append(f"        <variable {var_attrs}/>")
        lines.extend(f'        <key name="{name}" script="{script}"/>' for name, script in _entity_keys(spec))
        lines.append("    </generate>")
    lines.append("</setup>")
    return "\n".join(lines) + "\n"
