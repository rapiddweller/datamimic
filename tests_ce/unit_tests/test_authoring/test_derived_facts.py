# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Regression coverage for compiler-derived scaffold facts."""

import pytest
from pydantic import ValidationError

from datamimic_ce.authoring.contracts import (
    DerivedMemstoreFact,
    DerivedProductFact,
    ScaffoldRequest,
)
from datamimic_ce.authoring.derived_facts import derive_facts
from datamimic_ce.authoring.service import compile_document, scaffold


@pytest.mark.parametrize(
    "fact",
    [
        {"name": "rows", "kind": "time_series", "row_count": 2},
        {"name": "rows", "kind": "generated", "row_count": 2, "series_count": 1},
    ],
)
def test_product_fact_series_count_is_limited_to_time_series(fact: dict[str, object]) -> None:
    with pytest.raises(ValidationError, match="series_count"):
        DerivedProductFact.model_validate(fact)


def test_memstore_consumer_flag_must_match_its_consumers() -> None:
    with pytest.raises(ValidationError, match="has_consumer"):
        DerivedMemstoreFact(
            id="store",
            producer_product="users",
            consumer_products=[],
            has_consumer=True,
        )


def test_time_series_facts_use_the_compiler_static_cardinality() -> None:
    result = scaffold(
        ScaffoldRequest(
            spec={
                "version": "1",
                "seed": 7,
                "products": [
                    {
                        "kind": "time_series",
                        "name": "readings",
                        "series_count": 2,
                        "window": {
                            "start": "2025-01-01T00:00:00",
                            "end": "2025-01-01T06:00:00",
                            "interval": "PT1H",
                        },
                        "fields": [
                            {"kind": "values", "name": "sensor", "values": ["a", "b"]},
                            {"kind": "decimal_range", "name": "value", "minimum": 1, "maximum": 2},
                        ],
                    }
                ],
            },
            max_count=12,
        )
    )

    assert result.derived_facts is not None
    assert result.derived_facts.products[0].model_dump(mode="json", exclude_none=True) == {
        "name": "readings",
        "kind": "time_series",
        "row_count": 12,
        "series_count": 2,
    }


def test_memstore_and_foreign_key_facts_come_only_from_compiled_bindings_and_roles() -> None:
    document = compile_document(
        {
            "version": "1",
            "products": [
                {
                    "kind": "generated",
                    "name": "users",
                    "count": 2,
                    "targets": [{"kind": "memstore", "id": "store"}],
                    "fields": [
                        {"kind": "increment", "name": "id", "roles": [{"kind": "identifier"}]}
                    ],
                },
                {
                    "kind": "source",
                    "name": "user_audit",
                    "source": {"kind": "memstore", "id": "store", "product": "users"},
                    "fields": [
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
                    ],
                },
                {
                    "kind": "generated",
                    "name": "orphaned",
                    "count": 1,
                    "targets": [{"kind": "memstore", "id": "unused"}],
                    "fields": [{"kind": "increment", "name": "id"}],
                },
            ],
        }
    )

    facts = derive_facts(document.plan)

    assert [item.model_dump(mode="json") for item in facts.memstores] == [
        {
            "id": "store",
            "producer_product": "users",
            "consumer_products": ["user_audit"],
            "has_consumer": True,
        },
        {
            "id": "unused",
            "producer_product": "orphaned",
            "consumer_products": [],
            "has_consumer": False,
        },
    ]
    assert [item.model_dump(mode="json") for item in facts.foreign_keys] == [
        {
            "child_product": "user_audit",
            "child_field": "id",
            "parent_product": "users",
            "parent_field": "id",
        }
    ]


def test_unknown_file_source_cardinality_is_explicit_in_json_output() -> None:
    document = compile_document(
        {
            "version": "1",
            "products": [
                {
                    "kind": "source",
                    "name": "external_rows",
                    "source": {"kind": "file", "path": "external.csv"},
                    "fields": [{"kind": "script", "name": "id", "script": "this.id"}],
                }
            ],
        }
    )

    payload = derive_facts(document.plan).model_dump(mode="json", exclude_none=True)

    assert payload["products"] == [
        {"name": "external_rows", "kind": "source", "row_count": None}
    ]
