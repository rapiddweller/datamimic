# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
"""Gate: every field documented in docs/data-domains/domain_models.md's entity
field trees is a real attribute on the corresponding generated entity.

Entity -> service class comes from the same registry the DSL uses to resolve
`entity="Person"` (datamimic_ce.domains.domain_core.entity_registry), so this
gate cannot drift from the code the way a hand-maintained doc can. Only the
forward direction is checked (documented field must exist); an undocumented
real attribute is not a failure — this doc is allowed to be a subset.
"""

from __future__ import annotations

import random
import re
from pathlib import Path

from datamimic_ce.domains.domain_core.entity_registry import get_entity_spec

DOC_PATH = Path(__file__).resolve().parents[3] / "docs" / "data-domains" / "domain_models.md"

# "#### EntityName" heading, a blank line, then a fenced field-tree block:
#   EntityName
#   ├── field: type
#   └── field: type
HEADING_AND_TREE_RE = re.compile(r"^#### (\w+)\s*\n\n```\n(.*?)\n```", re.M | re.S)
TREE_LINE_RE = re.compile(r"^[│├└]*[├└]── (\w+)")

SEED = random.Random(42)


def _parse_entity_field_trees() -> dict[str, list[str]]:
    text = DOC_PATH.read_text()
    entities: dict[str, list[str]] = {}
    for match in HEADING_AND_TREE_RE.finditer(text):
        entity_name, tree_body = match.group(1), match.group(2)
        fields = [m.group(1) for line in tree_body.splitlines() if (m := TREE_LINE_RE.match(line))]
        entities[entity_name] = fields
    return entities


def test_domain_models_doc_parses_a_reasonable_number_of_entities():
    entities = _parse_entity_field_trees()
    total_fields = sum(len(fields) for fields in entities.values())
    # Guard against the parser silently matching nothing (a vacuous, always-green gate).
    assert len(entities) >= 15, f"only parsed {len(entities)} entities; markdown parser is likely broken"
    assert total_fields >= 100, f"only parsed {total_fields} fields across all entities; parser is likely broken"


def test_documented_fields_exist_on_the_real_entity():
    entities = _parse_entity_field_trees()
    assert entities, "no entities parsed from domain_models.md — see previous test"

    failures = []
    checked = 0
    for entity_name, fields in entities.items():
        spec = get_entity_spec(entity_name)
        if spec is None:
            # Documented heading has no registered CE service behind it (e.g. an
            # EE-only or conceptual entity) — currently none of the 21 headings
            # in domain_models.md hit this; skip rather than fail if one does.
            continue
        checked += 1

        instance = spec.service_cls(dataset="US", rng=random.Random(SEED.random())).generate()
        for field in fields:
            if not hasattr(instance, field):
                failures.append(f"{entity_name}.{field} (docs/data-domains/domain_models.md)")

    assert not failures, "documented field(s) do not exist on the real entity:\n" + "\n".join(failures)
    assert checked >= 15, f"only {checked} entities had a resolvable CE service; expected the full 21-entity doc"
