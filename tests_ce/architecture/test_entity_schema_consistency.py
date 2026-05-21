# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Gate: each entity's schema is the single source of truth for its fields.

Every key a model's ``to_dict()`` emits must be declared in the entity's
schema (``attribute_specs()``). This keeps the declared schema and the runtime
model from drifting. Schemas may declare *more* than a given instance emits
(conditional fields such as Transaction.account / Patient.primary_doctor), so
the contract is ``emitted_keys ⊆ declared_names``.
"""

from __future__ import annotations

from random import Random

import pytest

from datamimic_ce.domains.domain_core.attribute_catalog import FieldSpec
from datamimic_ce.domains.domain_core.entity_registry import list_entity_specs

_SEED = 20260521


@pytest.mark.parametrize("spec", list_entity_specs(), ids=lambda s: s.entity)
def test_schema_declares_every_emitted_key(spec) -> None:
    declared = {f.name for f in spec.attributes}
    assert declared, f"{spec.entity} declares no schema fields"

    emitted = set(spec.service_cls(rng=Random(_SEED)).generate().to_dict().keys())
    undeclared = emitted - declared
    assert not undeclared, (
        f"{spec.entity}.to_dict() emits keys missing from its schema: {sorted(undeclared)} "
        f"— update the entity's EntitySchema."
    )


def _type_matches(value: object, fs: FieldSpec) -> bool:
    """Whether an emitted value matches the field's declared python type."""
    if value is None:
        return fs.optional
    if fs.children:  # nested group is declared dict-valued
        return isinstance(value, dict)
    expected = fs.py_type if isinstance(fs.py_type, tuple) else (fs.py_type,)
    # A whole-number value satisfies a declared float (JSON numbers don't distinguish).
    if float in expected and isinstance(value, int) and not isinstance(value, bool):
        return True
    return isinstance(value, expected)


@pytest.mark.parametrize("spec", list_entity_specs(), ids=lambda s: s.entity)
def test_emitted_value_types_match_schema(spec) -> None:
    """The schema's declared type must match the runtime type the model emits.

    Guards against a schema that lies about a field's type (e.g. declaring a
    date field ``str`` while the model emits ``datetime``). ``to_dict()`` only
    sees key names; this gate is the only thing checking declared types.
    """
    by_name: dict[str, FieldSpec] = {f.name: f for f in spec.attributes}
    emitted = spec.service_cls(rng=Random(_SEED)).generate().to_dict()

    mismatches = [
        f"{name}: declared {by_name[name].data_type!r}, got {type(value).__name__}"
        for name, value in emitted.items()
        if name in by_name and not _type_matches(value, by_name[name])
    ]
    assert not mismatches, (
        f"{spec.entity} schema type(s) disagree with emitted values: {mismatches} "
        f"— fix the EntitySchema field type or the generator."
    )
