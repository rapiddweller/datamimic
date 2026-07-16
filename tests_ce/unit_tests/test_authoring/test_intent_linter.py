"""Intent-level authoring diagnostics remain actionable through scaffold."""

from datamimic_ce.authoring.contracts import ScaffoldRequest
from datamimic_ce.authoring.rule_catalog import RuleSeverity
from datamimic_ce.authoring.service import scaffold


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
