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
