# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""DSL-expressed determinism contract.

The seeded-replay contract is described as a readable DATAMIMIC DSL model
(``all_entities_seeded.xml``): every registered domain entity is generated with
an ``rngSeed`` and a handful of scalar fields. Entities with a non-optional
grouped field (e.g. a structured address) also expose one nested scalar via a
script (``e.address.street``), so the contract covers nested attribute access
through the model — which resolves via the entity's properties and is
independent of how ``to_dict()`` serialises that nested record. Running the same
model twice must yield byte-identical output per ``<generate>`` block.

The model is GENERATED from the entity registry (``build_all_entities_seeded_xml``)
and the generated text is committed so a reviewer can read it top-to-bottom. A
sync-check test fails if the committed file drifts from the registry, so a newly
added entity must be regenerated in — it cannot silently skip the gate.

Regenerate the committed model after adding/removing an entity::

    python tests_ce/integration_tests/test_determinism_dsl/test_determinism_dsl.py

NOTE: this gate runs single-process (``multiprocessing="0"``). Cross-process
determinism (``numProcess`` > 1) is a separate, currently-unmet contract and is
NOT exercised here — see the review notes on multiprocessing seeding.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest
from datamimic_ce.domains.domain_core.entity_registry import EntitySpec, list_entity_specs

_MODEL_FILENAME = "all_entities_seeded.xml"
_MODEL_PATH = Path(__file__).resolve().parent / _MODEL_FILENAME

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


def _candidate_nested_paths(field: str, value: object):
    """Yield ``(name_suffix, script_expr)`` candidates for one nested field.

    Reflects how a DSL script reaches a scalar inside a sub-structure:
    sub-objects via attribute access (``e.address.street``), plain data dicts
    via item access (``e.office_hours['Monday']``), and lists via ``[0]``.
    """
    if _is_entity_obj(value):
        for s in _scalar_subkeys(value):
            yield f"{field}_{s}", f"e.{field}.{s}"
    elif isinstance(value, dict):
        for s in _scalar_subkeys(value):
            yield f"{field}_{_slug(s)}", f"e.{field}[{s!r}]"
    elif isinstance(value, list) and value:
        item = value[0]
        if _is_entity_obj(item):
            for s in _scalar_subkeys(item):
                yield f"{field}_0_{s}", f"e.{field}[0].{s}"
        elif isinstance(item, dict):
            for s in _scalar_subkeys(item):
                yield f"{field}_0_{_slug(s)}", f"e.{field}[0][{s!r}]"
        elif _is_scalar(item):
            yield f"{field}_0", f"e.{field}[0]"


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
        candidate = next(iter(_candidate_nested_paths(field, prop)), None)
        if candidate is not None:
            nested.append(candidate)

    keys = scalars + nested
    while failing := _failing_keys(spec, keys):
        keys = [k for k in keys if k[0] not in failing]
    return keys


def build_all_entities_seeded_xml() -> str:
    """Render the seeded-replay DSL model from the entity registry.

    One ``<generate>`` block per registered entity (sorted by name), each seeded
    with ``rngSeed`` and exposing the first few scalar fields from its schema.
    Each entity additionally exposes one scalar reached *through* every reliably
    accessible sub-structure (sub-objects, data dicts, lists), so the contract
    covers nested access — which resolves via the model's properties and is
    independent of how ``to_dict()`` serialises those nested records.
    """
    lines = [
        '<setup multiprocessing="0">',
        "    <!-- AUTO-GENERATED from the entity registry by build_all_entities_seeded_xml(). -->",
        "    <!-- Do not edit by hand; regenerate via test_determinism_dsl.py (see module docstring). -->",
    ]
    for spec in sorted(list_entity_specs(), key=lambda s: s.entity):
        lines.append(f'    <generate name="{spec.entity.lower()}" count="{COUNT}" target="">')
        lines.append(f'        <variable name="e" entity="{spec.entity}" dataset="US" rngSeed="{SEED}"/>')
        lines.extend(f'        <key name="{name}" script="{script}"/>' for name, script in _entity_keys(spec))
        lines.append("    </generate>")
    lines.append("</setup>")
    return "\n".join(lines) + "\n"


class TestDeterminismDsl:
    _test_dir = Path(__file__).resolve().parent

    def _run(self, filename: str) -> dict:
        engine = DataMimicTest(test_dir=self._test_dir, filename=filename, capture_test_result=True)
        engine.test_with_timer()
        return engine.capture_result()

    def test_committed_model_is_in_sync_with_registry(self) -> None:
        """The committed XML must equal what the registry generates today.

        Guards against a new entity being added to the code but missing from the
        determinism model (and vice versa).
        """
        assert _MODEL_PATH.read_text() == build_all_entities_seeded_xml(), (
            f"{_MODEL_FILENAME} is out of sync with the entity registry. Regenerate it: "
            f"python tests_ce/integration_tests/test_determinism_dsl/test_determinism_dsl.py"
        )

    def test_all_entities_replay_identically(self) -> None:
        first = self._run(_MODEL_FILENAME)
        second = self._run(_MODEL_FILENAME)

        assert first.keys() == second.keys(), "Same model must produce the same generate blocks"
        assert first, "Expected the model to produce at least one entity block"
        for block, rows in first.items():
            assert rows, f"Block '{block}' produced no rows"
            assert rows == second[block], f"Seeded block '{block}' must replay identically"


if __name__ == "__main__":
    _MODEL_PATH.write_text(build_all_entities_seeded_xml())
    print(f"Wrote {_MODEL_PATH}")
