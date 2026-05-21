# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""DSL-expressed determinism contract.

The seeded-replay contract is described as a readable DATAMIMIC DSL model
(``all_entities_seeded.xml``): every registered domain entity is generated with
an ``rngSeed`` and a handful of scalar fields. Running the same model twice must
yield byte-identical output per ``<generate>`` block.

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

from datetime import date, datetime
from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest
from datamimic_ce.domains.domain_core.entity_registry import EntitySpec, list_entity_specs

_MODEL_FILENAME = "all_entities_seeded.xml"
_MODEL_PATH = Path(__file__).resolve().parent / _MODEL_FILENAME

SEED = 42
KEYS_PER_ENTITY = 3
_SCALAR_TYPES = (str, int, float, bool, datetime, date)


def _scalar_leaf_fields(spec: EntitySpec) -> list:
    """Leaf (non-grouped) fields with a scalar python type, in declared order."""
    return [
        f
        for f in spec.attributes
        if not f.children and isinstance(f.py_type, type) and issubclass(f.py_type, _SCALAR_TYPES)
    ]


def build_all_entities_seeded_xml() -> str:
    """Render the seeded-replay DSL model from the entity registry.

    One ``<generate>`` block per registered entity (sorted by name), each seeded
    with ``rngSeed`` and exposing the first few scalar fields from its schema.
    """
    lines = [
        '<setup multiprocessing="0">',
        "    <!-- AUTO-GENERATED from the entity registry by build_all_entities_seeded_xml(). -->",
        "    <!-- Do not edit by hand; regenerate via test_determinism_dsl.py (see module docstring). -->",
    ]
    for spec in sorted(list_entity_specs(), key=lambda s: s.entity):
        keys = _scalar_leaf_fields(spec)[:KEYS_PER_ENTITY]
        if not keys:
            raise ValueError(f"Entity '{spec.entity}' exposes no scalar field to seed the determinism model with.")
        lines.append(f'    <generate name="{spec.entity.lower()}" count="3" target="">')
        lines.append(f'        <variable name="e" entity="{spec.entity}" dataset="US" rngSeed="{SEED}"/>')
        lines.extend(f'        <key name="{f.name}" script="e.{f.name}"/>' for f in keys)
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
