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

import json
from random import Random
from types import MappingProxyType

import pytest

from datamimic_ce.domains.domain_core.contracts.attribute_catalog import FieldSpec
from datamimic_ce.domains.finance.generators.bank_account_generator import BankAccountGenerator
from datamimic_ce.domains.finance.generators.transaction_generator import TransactionGenerator
from datamimic_ce.domains.finance.models.bank_account import BankAccount
from datamimic_ce.domains.finance.models.transaction import Transaction
from datamimic_ce.domains.finance.services.transaction_service import TRANSACTION_SCHEMA
from datamimic_ce.domains.healthcare.services.patient_service import PatientService
from datamimic_ce.domains.registry.entities import list_entity_specs
from datamimic_ce.domains.shared.demographics.config import DemographicConfig
from datamimic_ce.domains.shared.services.person_service import PersonService

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


def test_linked_transaction_account_matches_nested_schema() -> None:
    transaction = Transaction(
        TransactionGenerator(rng=Random(_SEED)),
        BankAccount(BankAccountGenerator(rng=Random(_SEED))),
    )
    account = transaction.to_dict()["account"]
    account_spec = next(field for field in TRANSACTION_SCHEMA.fields if field.name == "account")

    assert isinstance(account, dict)
    declared = {field.name: field for field in account_spec.children}
    assert set(account) == set(declared)
    assert all(_type_matches(value, declared[name]) for name, value in account.items())


def test_unlinked_transaction_omits_account() -> None:
    transaction = Transaction(TransactionGenerator(rng=Random(_SEED)))

    assert "account" not in transaction.to_dict()


@pytest.mark.parametrize("service_type", (PersonService, PatientService))
@pytest.mark.parametrize("profile_kind", ("none", "string", "dict", "mapping"))
def test_configured_transaction_profile_matches_schema(service_type, profile_kind: str) -> None:
    backing = {"daily": 0.5}
    profile = {
        "none": None,
        "string": "student",
        "dict": backing,
        "mapping": MappingProxyType(backing),
    }[profile_kind]
    config = DemographicConfig(transaction_profile=profile)
    defaulted = config.with_defaults(default_age_min=30, default_age_max=50)
    assert defaulted is not config
    assert defaulted.transaction_profile is profile
    assert (defaulted.age_min, defaulted.age_max) == (30, 50)
    assert (config.age_min, config.age_max) == (None, None)
    service = service_type(dataset="US", demographic_config=config, rng=Random(_SEED))
    entity = service.generate()
    value = entity.transaction_profile
    assert value is profile

    if profile_kind in ("dict", "mapping"):
        backing["daily"] = 0.75
        assert entity.transaction_profile is value
        assert value["daily"] == 0.75
    if profile_kind == "mapping":
        with pytest.raises(TypeError, match="not JSON serializable"):
            json.dumps(value)
    else:
        expected_json = {"none": "null", "string": '"student"', "dict": '{"daily": 0.75}'}
        assert json.dumps(value) == expected_json[profile_kind]

    spec = next(field for field in service.attribute_specs() if field.name == "transaction_profile")
    assert _type_matches(value, spec), f"{type(value).__name__} does not satisfy {spec.data_type}"
    if profile_kind == "mapping":
        assert entity.to_dict()["transaction_profile"] is value
