"""Intent-level authoring diagnostics remain actionable through scaffold."""

import json
from pathlib import Path

from datamimic_ce.authoring.contracts import ScaffoldRequest
from datamimic_ce.authoring.domain.rule_catalog import RuleSeverity
from datamimic_ce.authoring.application.service import scaffold

_FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _model_fixture(name: str) -> dict[str, object]:
    return json.loads((_FIXTURES / name).read_text(encoding="utf-8"))


def test_memstore_target_without_consumer_blocks_verified_with_exact_diagnostic() -> None:
    result = scaffold(ScaffoldRequest(spec=_model_fixture("fx_memstore_target_without_consumer.model.dm.json")))

    diagnostics = [item for item in result.diagnostics if item.rule == "DM408"]
    assert len(diagnostics) == 1
    diagnostic = diagnostics[0]
    assert diagnostic.severity is RuleSeverity.WARNING
    assert diagnostic.path == "/products/0/targets/0"
    assert diagnostic.name == "store"
    assert diagnostic.message == (
        "A product writes to a memstore that no source product reads, so the write is unobservable in the "
        "authoring model. Evidence: users writes memstore 'store', but no product reads it"
    )
    assert diagnostic.fix_hint == "Add a source product that reads the memstore, or remove the unused memstore target."
    assert result.ok is True
    assert result.acceptance is not None and result.acceptance.verified is True
    assert result.verified is False


def test_memstore_target_with_consumer_does_not_block_verified() -> None:
    result = scaffold(ScaffoldRequest(spec=_model_fixture("fx_memstore_target_with_consumer.model.dm.json")))

    assert not [item for item in result.diagnostics if item.rule == "DM408"]
    assert result.verified is True


def _memstore_readback_spec(*, copy_source: bool) -> dict[str, object]:
    readback_fields: list[dict[str, object]] = [
        {
            "kind": "script",
            "name": "id",
            "script": "this.id",
            "roles": [
                {
                    "kind": "foreign_key",
                    "parent_product": "users",
                    "parent_field": "id",
                }
            ],
        }
    ]
    for name, values in (("region", ["eu", "us", "apac"]), ("credit_limit", None)):
        if copy_source:
            readback_fields.append({"kind": "script", "name": name, "script": f"this.{name}"})
        elif values is not None:
            readback_fields.append({"kind": "values", "name": name, "values": values})
        else:
            readback_fields.append({"kind": "int_range", "name": name, "minimum": 100, "maximum": 1000})
    return {
        "version": "1",
        "seed": 7,
        "products": [
            {
                "kind": "generated",
                "name": "users",
                "count": 2,
                "fields": [
                    {"kind": "increment", "name": "id", "roles": [{"kind": "identifier"}]},
                    {"kind": "values", "name": "region", "values": ["eu", "us", "apac"]},
                    {"kind": "int_range", "name": "credit_limit", "minimum": 100, "maximum": 1000},
                ],
                "targets": [{"kind": "memstore", "id": "store"}],
            },
            {
                "kind": "source",
                "name": "user_audit",
                "source": {"kind": "memstore", "id": "store", "product": "users"},
                "fields": readback_fields,
            },
        ],
    }


def test_random_nested_foreign_key_warns_before_acceptance() -> None:
    result = scaffold(
        ScaffoldRequest(
            spec={
                "version": "1",
                "seed": 7,
                "products": [
                    {
                        "kind": "generated",
                        "name": "customers",
                        "count": 2,
                        "fields": [{"kind": "increment", "name": "id"}],
                        "children": [
                            {
                                "name": "orders",
                                "count": 2,
                                "fields": [
                                    {
                                        "kind": "int_range",
                                        "name": "customer_id",
                                        "minimum": 1,
                                        "maximum": 2,
                                        "roles": [
                                            {
                                                "kind": "foreign_key",
                                                "parent_product": "customers",
                                                "parent_field": "id",
                                            }
                                        ],
                                    }
                                ],
                            }
                        ],
                    }
                ],
                "expectations": [
                    {
                        "kind": "per_parent_count",
                        "parent_product": "customers",
                        "child_product": "orders",
                        "count": 2,
                    }
                ],
            }
        )
    )

    diagnostic = next(item for item in result.diagnostics if item.rule == "DM404")
    assert diagnostic.severity is RuleSeverity.WARNING
    assert diagnostic.path == "/products/0/children/0/fields/0"
    assert 'script: "parent.id"' in diagnostic.fix_hint
    assert result.acceptance is not None
    assert result.verified is False


def test_nested_foreign_key_script_must_exactly_copy_its_immediate_parent_key() -> None:
    spec = {
        "version": "1",
        "seed": 7,
        "products": [
            {
                "kind": "generated",
                "name": "customers",
                "count": 2,
                "fields": [{"kind": "increment", "name": "id"}],
                "children": [
                    {
                        "name": "orders",
                        "count": 1,
                        "fields": [
                            {
                                "kind": "script",
                                "name": "customer_id",
                                "script": "parent.id + 1",
                                "roles": [
                                    {
                                        "kind": "foreign_key",
                                        "parent_product": "customers",
                                        "parent_field": "id",
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        ],
    }

    result = scaffold(ScaffoldRequest(spec=spec))

    assert [item.rule for item in result.diagnostics if item.rule == "DM404"] == ["DM404"]
    assert result.verified is False


def test_nested_foreign_key_direct_parent_copy_has_no_diagnostic() -> None:
    spec = {
        "version": "1",
        "seed": 7,
        "products": [
            {
                "kind": "generated",
                "name": "customers",
                "count": 2,
                "fields": [{"kind": "increment", "name": "id"}],
                "children": [
                    {
                        "name": "orders",
                        "count": 1,
                        "fields": [
                            {
                                "kind": "script",
                                "name": "customer_id",
                                "script": "parent.id",
                                "roles": [
                                    {
                                        "kind": "foreign_key",
                                        "parent_product": "customers",
                                        "parent_field": "id",
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        ],
    }

    result = scaffold(ScaffoldRequest(spec=spec))

    assert not [item for item in result.diagnostics if item.rule == "DM404"]
    assert result.verified is True


def test_memstore_readback_regeneration_warns_with_an_exact_copy_repair() -> None:
    result = scaffold(ScaffoldRequest(spec=_memstore_readback_spec(copy_source=False)))

    diagnostics = [item for item in result.diagnostics if item.rule == "DM406"]
    assert {item.name for item in diagnostics} == {"region", "credit_limit"}
    assert all(item.severity is RuleSeverity.WARNING for item in diagnostics)
    assert '"script":"this.region"' in diagnostics[0].fix_hint
    assert result.ok is True
    assert result.acceptance is not None and result.acceptance.verified is True
    assert result.verified is False


def test_memstore_readback_copy_fields_do_not_warn() -> None:
    result = scaffold(ScaffoldRequest(spec=_memstore_readback_spec(copy_source=True)))

    assert result.verified is True
    assert not [item for item in result.diagnostics if item.rule == "DM406"]


def test_memstore_readback_rule_accepts_bare_source_field_reference() -> None:
    spec = _memstore_readback_spec(copy_source=True)
    audit = spec["products"][1]
    assert isinstance(audit, dict)
    fields = audit["fields"]
    assert isinstance(fields, list)
    fields[1]["script"] = "region"

    result = scaffold(ScaffoldRequest(spec=spec))

    assert result.verified is True
    assert not [item for item in result.diagnostics if item.rule == "DM406"]


def test_memstore_readback_rule_accepts_source_derived_transform() -> None:
    spec = _memstore_readback_spec(copy_source=True)
    audit = spec["products"][1]
    assert isinstance(audit, dict)
    fields = audit["fields"]
    assert isinstance(fields, list)
    fields[1]["script"] = "this.region.upper()"

    result = scaffold(ScaffoldRequest(spec=spec))

    assert result.verified is True
    assert not [item for item in result.diagnostics if item.rule == "DM406"]


def test_memstore_readback_rule_uses_compiler_resolution_without_explicit_producer() -> None:
    spec = _memstore_readback_spec(copy_source=False)
    audit = spec["products"][1]
    assert isinstance(audit, dict)
    source = audit["source"]
    assert isinstance(source, dict)
    del source["product"]

    result = scaffold(ScaffoldRequest(spec=spec))

    diagnostics = [item for item in result.diagnostics if item.rule == "DM406"]
    assert {item.name for item in diagnostics} == {"region", "credit_limit"}


def test_memstore_readback_rule_uses_compiler_resolution_for_nested_producer() -> None:
    result = scaffold(
        ScaffoldRequest(
            spec={
                "version": "1",
                "products": [
                    {
                        "kind": "generated",
                        "name": "customers",
                        "count": 1,
                        "fields": [{"kind": "increment", "name": "id"}],
                        "children": [
                            {
                                "name": "snapshots",
                                "count": 1,
                                "fields": [{"kind": "values", "name": "region", "values": ["eu"]}],
                                "targets": [{"kind": "memstore", "id": "snapshot_store"}],
                            }
                        ],
                    },
                    {
                        "kind": "source",
                        "name": "snapshot_audit",
                        "source": {"kind": "memstore", "id": "snapshot_store"},
                        "fields": [{"kind": "values", "name": "region", "values": ["us"]}],
                    },
                ],
            }
        )
    )

    diagnostics = [item for item in result.diagnostics if item.rule == "DM406"]
    assert [item.name for item in diagnostics] == ["region"]


def test_memstore_readback_repair_preserves_field_roles() -> None:
    spec = _memstore_readback_spec(copy_source=False)
    audit = spec["products"][1]
    assert isinstance(audit, dict)
    fields = audit["fields"]
    assert isinstance(fields, list)
    fields[0] = {
        "kind": "int_range",
        "name": "id",
        "minimum": 1,
        "maximum": 2,
        "roles": fields[0]["roles"],
    }

    result = scaffold(ScaffoldRequest(spec=spec))

    foreign_key = next(item for item in result.diagnostics if item.rule == "DM406" and item.name == "id")

    assert '"roles":[{"kind":"foreign_key"' in foreign_key.fix_hint


def test_memstore_readback_rule_allows_consumer_only_derived_fields() -> None:
    spec = _memstore_readback_spec(copy_source=True)
    audit = spec["products"][1]
    assert isinstance(audit, dict)
    fields = audit["fields"]
    assert isinstance(fields, list)
    fields.append({"kind": "constant", "name": "ingest_channel", "value": "memstore"})

    result = scaffold(ScaffoldRequest(spec=spec))

    assert result.verified is True
    assert not [item for item in result.diagnostics if item.rule == "DM406"]


def _delivery_spec(*, parent_targets: list[dict[str, object]], child_targets: list[dict[str, object]]) -> dict:
    return {
        "version": "1",
        "seed": 7,
        "products": [
            {
                "kind": "generated",
                "name": "customers",
                "count": 2,
                "targets": parent_targets,
                "fields": [{"kind": "increment", "name": "id", "roles": [{"kind": "identifier"}]}],
                "children": [
                    {
                        "kind": "generated",
                        "name": "accounts",
                        "count": 2,
                        "targets": child_targets,
                        "fields": [
                            {
                                "kind": "script",
                                "name": "customer_id",
                                "script": "parent.id",
                                "roles": [{"kind": "foreign_key", "parent_product": "customers", "parent_field": "id"}],
                            }
                        ],
                    }
                ],
            }
        ],
    }


_JSON = [{"kind": "file_export", "format": "JSON"}]


def test_undelivered_child_of_an_exporting_parent_blocks_verification() -> None:
    result = scaffold(ScaffoldRequest(spec=_delivery_spec(parent_targets=_JSON, child_targets=[])))

    diagnostics = [item for item in result.diagnostics if item.rule == "DM407"]
    assert [(item.name, item.path) for item in diagnostics] == [("accounts", "/products/0/children/0")]
    assert result.acceptance is not None and result.acceptance.verified is True
    assert result.verified is False


def test_every_product_with_a_target_verifies() -> None:
    result = scaffold(ScaffoldRequest(spec=_delivery_spec(parent_targets=_JSON, child_targets=_JSON)))

    assert not [item for item in result.diagnostics if item.rule == "DM407"]
    assert result.verified is True


def test_spec_without_file_export_is_an_in_memory_model() -> None:
    result = scaffold(ScaffoldRequest(spec=_delivery_spec(parent_targets=[], child_targets=[])))

    assert not [item for item in result.diagnostics if item.rule == "DM407"]
    assert result.verified is True
