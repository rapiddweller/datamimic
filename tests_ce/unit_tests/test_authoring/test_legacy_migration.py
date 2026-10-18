"""Legacy proof facts survive independently from generated XML."""

import importlib.util
from pathlib import Path

import pytest
from pydantic import ValidationError


def _migration():
    path = Path(__file__).resolve().parents[3] / "script" / "migrate_authoring.py"
    spec = importlib.util.spec_from_file_location("migrate_authoring", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_translates_counts_and_field_roles_to_transaction_data() -> None:
    result = _migration().transaction_from_legacy({
        "expectations": [{"kind": "unique", "product": "customers", "field": "name", "list_field": "contacts", "scope": "per_parent"}],
        "plan": {"products": [{"name": "customers", "fields": [{"name": "id", "roles": [{"kind": "identifier"}]}]}],
                 "derived_acceptance": [{"kind": "exact_count", "product": "customers", "exact_count": 3}],
                 "relationships": [], "unresolved": []},
    })
    assert result["product_roles"] == [{"product": "customers", "field": "id", "role": {"kind": "identifier"}}]
    assert result["expectations"] == [{"kind": "unique", "subject": {"kind": "product", "product": "customers", "list_field": "contacts"}, "field": "name", "scope": "per_parent"}]
    assert result["acceptance_requirements"] == [{"origin": "derived", "expectation": {"kind": "exact_count", "subject": {"kind": "product", "product": "customers"}, "count": 3}}]


def test_translates_nested_fk_and_per_parent_identity() -> None:
    result = _migration().transaction_from_legacy({
        "expectations": [{"kind": "foreign_key", "child_product": "accounts", "child_field": "customer_id", "parent_product": "customers", "parent_field": "id"}],
        "plan": {"products": [], "derived_acceptance": [{"kind": "per_parent_count", "product": "accounts", "parent_product": "customers", "count_per_parent": 2}], "relationships": [], "unresolved": []},
    })
    assert result["expectations"][0] == {"kind": "foreign_key", "child": {"subject": {"kind": "product", "product": "accounts"}, "field": "customer_id"}, "parent": {"subject": {"kind": "product", "product": "customers"}, "field": "id"}}
    assert result["acceptance_requirements"][0]["expectation"]["subject"] == {"kind": "per_parent", "parent_product": "customers", "child_product": "accounts"}


def test_unknown_legacy_expectation_fails_with_a_path() -> None:
    with pytest.raises(ValueError, match=r"expectations\[0\]"):
        _migration().transaction_from_legacy({"expectations": [{"kind": "unsupported"}], "plan": {"products": [], "derived_acceptance": [], "relationships": [], "unresolved": []}})


def test_translated_receipt_is_accepted_by_new_build_contract() -> None:
    from datamimic_ce.authoring.domain.requests import BuildRequestV4

    transaction = _migration().transaction_from_legacy({"expectations": [], "plan": {"products": [], "derived_acceptance": [{"kind": "range", "product": "accounts", "field": "amount", "minimum": "0.10", "maximum": "99.90"}], "relationships": [], "unresolved": []}})
    request = BuildRequestV4.model_validate({"document": {"root": {"kind": "setup"}}, **transaction})
    assert str(request.acceptance_requirements[0].expectation.minimum) == "0.10"


def test_rejects_unknown_expectation_fields_without_dropping_them() -> None:
    with pytest.raises(ValueError, match=r"expectations\[0\]\.subject"):
        _migration().transaction_from_legacy({
            "expectations": [{"kind": "unique", "product": "rows", "field": "id", "subject": {"kind": "product", "product": "other"}}],
            "plan": {"products": [], "derived_acceptance": [], "relationships": [], "unresolved": []},
        })


def test_translates_caller_requirements_without_persisting_them_as_model_expectations() -> None:
    result = _migration().transaction_from_legacy({
        "expectations": [],
        "acceptance_requirements": [{"kind": "per_parent_count", "parent_product": "parents", "child_product": "children", "count": 2}],
        "plan": {"products": [], "derived_acceptance": [], "relationships": [], "unresolved": []},
    })
    assert result["expectations"] == []
    assert result["acceptance_requirements"] == [{"origin": "caller", "expectation": {
        "kind": "per_parent_count", "subject": {"kind": "per_parent", "parent_product": "parents", "child_product": "children"}, "count": 2,
    }}]


def test_preserves_roles_inside_nested_lists() -> None:
    result = _migration().transaction_from_legacy({
        "expectations": [],
        "plan": {"products": [{"name": "rows", "fields": [{"name": "id", "list_field": "items", "roles": [{"kind": "identifier"}]}]}], "derived_acceptance": [], "relationships": [], "unresolved": []},
    })
    assert result["product_roles"] == [{"product": "rows", "field": "id", "list_field": "items", "role": {"kind": "identifier"}}]


def test_rejects_malformed_role_at_its_input_path() -> None:
    with pytest.raises(ValueError, match=r"plan\.products\[0\]\.fields\[0\]\.roles\[0\]"):
        _migration().transaction_from_legacy({"expectations": [], "plan": {
            "products": [{"name": "rows", "fields": [{"name": "id", "roles": [{"kind": "foreign_key"}]}]}],
            "derived_acceptance": [], "relationships": [], "unresolved": [],
        }})


def test_migration_refuses_overwrite_before_starting_compiler(tmp_path: Path) -> None:
    original = tmp_path / "model.dm.json"
    original.write_text('{}')
    output = tmp_path / "runtime.xml"
    output.write_text('keep')
    with pytest.raises(ValueError, match="overwrite"):
        _migration().migrate(original, legacy_source=tmp_path, legacy_python=tmp_path / "absent", xml_output=output)
    assert original.read_text() == '{}'
    assert output.read_text() == 'keep'


def test_migration_rejects_relocated_xml_before_starting_compiler(tmp_path: Path) -> None:
    original = tmp_path / "model.dm.json"
    original.write_text('{}')
    directory = tmp_path / "elsewhere"
    directory.mkdir()
    with pytest.raises(ValueError, match="beside the original"):
        _migration().migrate(original, legacy_source=tmp_path, legacy_python=tmp_path / "absent", xml_output=directory / "runtime.xml")
    assert not (directory / "runtime.xml").exists()


def test_migration_requires_frozen_git_source(tmp_path: Path) -> None:
    import sys

    original = tmp_path / "model.dm.json"
    original.write_text('{}')
    output = tmp_path / "runtime.xml"
    with pytest.raises(ValueError, match="legacy_source: cannot verify frozen CE source"):
        _migration().migrate(original, legacy_source=tmp_path, legacy_python=Path(sys.executable), xml_output=output)
    assert not output.exists()
