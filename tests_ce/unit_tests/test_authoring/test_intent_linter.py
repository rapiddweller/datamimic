"""Intent-level authoring diagnostics remain actionable through scaffold."""

from datamimic_ce.authoring.contracts import ScaffoldRequest
from datamimic_ce.authoring.rule_catalog import RuleSeverity
from datamimic_ce.authoring.service import scaffold


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


def test_memstore_readback_regeneration_warns_with_an_exact_copy_repair() -> None:
    result = scaffold(ScaffoldRequest(spec=_memstore_readback_spec(copy_source=False)))

    diagnostics = [item for item in result.diagnostics if item.rule == "DM406"]
    assert {item.name for item in diagnostics} == {"region", "credit_limit"}
    assert all(item.severity is RuleSeverity.WARNING for item in diagnostics)
    assert '"script":"this.region"' in diagnostics[0].fix_hint


def test_memstore_readback_copy_fields_do_not_warn() -> None:
    result = scaffold(ScaffoldRequest(spec=_memstore_readback_spec(copy_source=True)))

    assert result.verified is True
    assert not [item for item in result.diagnostics if item.rule == "DM406"]


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
