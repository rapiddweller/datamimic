# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""The scaffold renderer must ALWAYS emit structurally-valid, dry-runnable DSL —
that is the whole point (a weak model chooses values, never touches XML)."""

import re

import pytest

from datamimic_ce.authoring import lint_source
from datamimic_ce.authoring.contracts import AuthoringStage, ScaffoldRequest
from datamimic_ce.authoring.dryrun import dry_run_source
from datamimic_ce.authoring.scaffold import render
from datamimic_ce.authoring.service import scaffold as scaffold_spec

_SPECS = {
    "weighted_person": {
        "seed": 1,
        "generates": [{
            "name": "customers", "count": 30, "target": "JSON",
            "fields": [
                {"name": "id", "kind": "increment"},
                {"name": "full_name", "kind": "person_name"},
                {"name": "age", "kind": "int_range", "min": 18, "max": 90},
                {"name": "country", "kind": "weighted",
                 "values": ["US", "DE", "VN"], "weights": [0.5, 0.3, 0.2]},
            ],
        }],
    },
    "nested_list": {
        "seed": 2,
        "generates": [{
            "name": "products", "count": 10, "target": "JSON",
            "fields": [
                {"name": "sku", "kind": "pattern", "pattern": "[A-Z]{3}-[0-9]{4}"},
                {"name": "price", "kind": "decimal_range", "min": 1, "max": 99},
                {"name": "reviews", "kind": "nested_list", "min": 1, "max": 3,
                 "fields": [{"name": "rating", "kind": "int_range", "min": 1, "max": 5}]},
            ],
        }],
    },
    "memstore_handoff": {
        "generates": [
            {"name": "src", "count": 12, "target": "mem",
             "fields": [{"name": "v", "kind": "int_range", "min": 1, "max": 9}]},
            {"name": "out", "count": 12, "target": "JSON",
             "fields": [{"name": "id", "kind": "increment"}]},
        ],
    },
    "value_escaping": {
        "generates": [{
            "name": "x", "count": 3, "target": "JSON",
            "fields": [
                {"name": "note", "kind": "constant", "value": 'a "quoted" & <angled> value'},
                {"name": "choice", "kind": "values", "values": ["it's a", "b"]},
            ],
        }],
    },
    "memstore_readback": {
        "generates": [
            {"name": "orders", "count": 6, "target": "mem,JSON",
             "fields": [
                 {"name": "id", "kind": "increment"},
                 {"name": "value", "kind": "int_range", "min": 1, "max": 100},
             ]},
            {"name": "doubled", "target": "JSON", "source": "mem", "source_type": "orders",
             "fields": [
                 {"name": "value", "kind": "script", "script": "value"},
                 {"name": "doubled", "kind": "script", "script": "value * 2"},
             ]},
        ],
    },
    "timeseries": {
        "generates": [{
            "name": "readings", "count": 2, "target": "JSON",
            "start": "2025-01-01T00:00:00", "end": "2025-01-02T00:00:00", "interval": "PT1H",
            "fields": [{"name": "at", "kind": "script", "script": "ts.now"}],
        }],
    },
    "nested_generate": {
        "generates": [{
            "name": "customers", "count": 4, "target": "JSON",
            "fields": [{"name": "id", "kind": "increment"}],
            "children": [{
                "name": "orders", "count": 2, "target": "JSON",
                "fields": [{"name": "customer_id", "kind": "script", "script": "parent.id"}],
            }],
        }],
    },
    "unique_range": {
        "generates": [{
            "name": "flights", "count": 10, "target": "JSON",
            "fields": [{"name": "seat", "kind": "int_range", "min": 1, "max": 20, "unique": True}],
        }],
    },
    "nested_person_in_list": {
        "generates": [{
            "name": "departments", "count": 3, "target": "JSON",
            "fields": [
                {"name": "head", "kind": "person_name"},
                {"name": "employees", "kind": "nested_list", "min": 3, "max": 3,
                 "fields": [{"name": "employee_name", "kind": "person_name"}]},
            ],
        }],
    },
    "nested_person_in_children": {
        "generates": [{
            "name": "regions", "count": 3, "target": "JSON",
            # Person field at BOTH the outer scope and the child scope: only this
            # ancestor/descendant combination can actually exercise the bare-name
            # shadowing rule (a child-only person field, with no ancestor of the same
            # name to shadow it, would pass even pre-fix — see the review that caught
            # this the first time this spec was written).
            "fields": [
                {"name": "id", "kind": "increment"},
                {"name": "regional_director", "kind": "person_name"},
            ],
            "children": [{
                "name": "managers", "count": 2, "target": "JSON",
                "fields": [
                    # Echo the parent id back so the test can group managers by region
                    # without relying on row-order assumptions.
                    {"name": "region_ref", "kind": "script", "script": "parent.id"},
                    {"name": "manager_name", "kind": "person_name"},
                ],
            }],
        }],
    },
}


@pytest.mark.parametrize("name", sorted(_SPECS))
def test_scaffold_renders_lint_clean_and_runnable(name: str) -> None:
    xml = render(_SPECS[name])
    result = lint_source(xml)
    errors = [d for d in result.diagnostics if d.severity.value == "error"]
    assert not errors, f"{name}: {[(d.rule, d.message) for d in errors]}\n{xml}"

    dr = dry_run_source(xml, max_count=4, sample_rows=1)
    assert dr.ok, f"{name}: {[d.message for d in dr.diagnostics]}\n{xml}"
    assert dr.products and all(p.count > 0 for p in dr.products)


def test_unknown_kind_is_rejected_instead_of_silently_changing_intent() -> None:
    with pytest.raises(ValueError, match="unsupported field kind 'totally_made_up'"):
        render({"generates": [{"name": "g", "count": 2, "target": "JSON",
                               "fields": [{"name": "f", "kind": "totally_made_up", "value": "x"}]}]})


def test_rng_seed_alias_is_explicitly_normalized() -> None:
    result = scaffold_spec(
        ScaffoldRequest(
            spec={"rngSeed": 42, "generates": [{"name": "g", "count": 1,
                  "fields": [{"name": "id", "kind": "increment"}]}]},
            dry_run=False,
        )
    )

    assert result.ok
    assert result.xml is not None and '<setup rngSeed="42">' in result.xml
    assert "root key 'rngSeed' normalized to 'seed'" in result.normalization_notes


@pytest.mark.parametrize(
    "spec, expected",
    [
        ({"typo": 1, "generates": []}, "unknown scaffold root key"),
        ({"generates": [{"name": "g", "count": 1, "typo": 1,
          "fields": [{"name": "id", "kind": "increment"}]}]}, "unknown key.*generate 'g'"),
        ({"generates": [{"name": "g", "count": 1,
          "fields": [{"name": "id", "kind": "increment", "typo": 1}]}]},
         "unknown or incompatible key.*field"),
    ],
)
def test_unknown_scaffold_keys_are_rejected(spec: dict, expected: str) -> None:
    with pytest.raises(ValueError, match=expected):
        render(spec)


@pytest.mark.parametrize(
    "spec, expected",
    [
        ({"seed": 42.9, "generates": []}, "seed.*valid integer"),
        ({"generates": [{"name": "g", "count": 2.9,
          "fields": [{"name": "id", "kind": "increment"}]}]}, "count.*valid integer"),
        ({"generates": [{"name": "g", "count": 1,
          "fields": [{"name": "n", "kind": "int_range"}]}]}, "requires explicit min and max"),
        ({"generates": [{"name": "g", "count": 1,
          "fields": [{"name": "n", "kind": "int_range", "min": 1.9, "max": 3}]}]},
         "minimum.*valid integer"),
        ({"generates": [{"name": "g", "count": 1,
          "fields": [{"name": "items", "kind": "nested_list", "min": 1, "max": 2}]}]},
         "fields.*at least 1"),
    ],
)
def test_lossy_or_incomplete_scaffold_values_are_rejected(spec: dict, expected: str) -> None:
    with pytest.raises(ValueError, match=expected):
        render(spec)


def test_render_normalizes_model_key_drift() -> None:
    # A local model's near-miss JSON (Ollama does not strictly enforce the schema):
    # "generate" singular, "weighted_values" kind, a filename target, "type"/"field" aliases.
    drifted = {
        "generate": [{
            "name": "customers", "count": 50, "target": "JSON",
            "fields": [
                {"field": "id", "type": "id"},
                {"name": "country", "kind": "weighted_values",
                 "values": ["US", "DE"], "weights": [3, 1]},
                {"name": "age", "kind": "int_range", "min": 18, "max": 90},
            ],
        }],
    }
    xml = render(drifted)
    assert 'target="JSON"' in xml and "IncrementGenerator" in xml  # target + kind aliases resolved
    result = lint_source(xml)
    assert result.ok, [(d.rule, d.message) for d in result.diagnostics]
    dr = dry_run_source(xml, max_count=3, sample_rows=1)
    assert dr.ok and dr.products[0].count == 3


def test_render_rejects_malformed_spec_instead_of_emitting_empty() -> None:
    # A weak model's off-schema JSON (e.g. {"kinds": [...]}) must raise, never
    # silently render an empty <setup> that then dry-runs "ok" with no data.
    for bad in ({}, {"generates": []}, {"kinds": [{"type": "increment"}]},
                {"generates": [{"count": 5}]}):
        with pytest.raises(ValueError):
            render(bad)


def test_unique_int_range_produces_distinct_values() -> None:
    # unique=True must actually render distribution="shuffle" (CE's real unique-numeric-
    # range mechanism) and produce genuinely distinct values, not just lint-clean XML —
    # a stress test found a model producing silent DUPLICATE seat numbers with no way to
    # express uniqueness at all; this is the regression that would have caught it.
    xml = render(_SPECS["unique_range"])
    assert 'distribution="shuffle"' in xml
    dr = dry_run_source(xml, max_count=10, sample_rows=10)
    assert dr.ok, [d.message for d in dr.diagnostics]
    seats = [row["seat"] for row in dr.products[0].sample]
    assert len(seats) == len(set(seats)), f"duplicate seats: {seats}"


def test_unique_too_small_for_count_raises_at_render() -> None:
    # A range smaller than the requested count would silently under-produce rows via
    # distribution="shuffle"'s natural exhaustion (StopIteration, no diagnostic anywhere)
    # — must fail loudly at render time instead, matching render()'s own "raise, never
    # silently emit something wrong" philosophy.
    spec = {"generates": [{"name": "x", "count": 50, "target": "JSON",
                           "fields": [{"name": "seat", "kind": "int_range", "min": 1, "max": 20,
                                       "unique": True}]}]}
    with pytest.raises(ValueError, match="unique"):
        render(spec)


def test_unique_inside_nested_list_is_rejected_explicitly() -> None:
    # unique= only makes sense on a top-level field: a shuffle sequence is one stateful
    # iterator shared across the whole statement, not reset per parent-record iteration,
    # so applying it inside a nested_list would draw from one shared pool across ALL
    # parents (silent under-production). Must FAIL explicitly with a clear error
    # message, not silently drop the constraint and render as if it didn't exist.
    spec = {"generates": [{"name": "flights", "count": 3, "target": "JSON",
                           "fields": [
                               {"name": "flight_no", "kind": "pattern", "pattern": "[A-Z]{2}[0-9]{4}"},
                               {"name": "passengers", "kind": "nested_list", "min": 2, "max": 2,
                                "fields": [{"name": "seat", "kind": "int_range", "min": 1, "max": 5,
                                            "unique": True}]},
                           ]}]}
    with pytest.raises(ValueError, match="unsupported feature.*unique.*nested"):
        render(spec)


def test_nested_person_in_list_gets_distinct_names_within_one_parent() -> None:
    # A stress test found every item in a nested list of people getting the SAME name —
    # the outer generate's single shared Person variable, reused (shadowed) instead of a
    # fresh one per nested scope. The discriminating property is WITHIN-parent
    # distinctness specifically: a union of names ACROSS multiple sampled departments
    # can look varied even when every single department's own employees are all the
    # identical (shadowed) person — verified empirically against the pre-fix code,
    # which passed a same-shaped "union across departments" assertion. Check each
    # department's own employee list directly instead.
    xml = render(_SPECS["nested_person_in_list"])
    assert lint_source(xml).ok, xml
    dr = dry_run_source(xml, max_count=3, sample_rows=3)
    assert dr.ok, [d.message for d in dr.diagnostics]

    per_department_name_counts = [
        len({e["employee_name"] for e in dept["employees"]}) for dept in dr.products[0].sample
    ]
    assert all(n > 1 for n in per_department_name_counts), (
        f"a department's own employees share one name: counts={per_department_name_counts}"
    )


def test_nested_person_in_children_gets_distinct_names_within_one_parent() -> None:
    # Same property as above, for the sibling nesting path (a child <generate>, not a
    # nested_list). Group the flat "managers" product by the region it belongs to (via
    # an echoed-back parent id) rather than assuming row order.
    xml = render(_SPECS["nested_person_in_children"])
    assert lint_source(xml).ok, xml
    dr = dry_run_source(xml, max_count=3, sample_rows=6)
    assert dr.ok, [d.message for d in dr.diagnostics]

    managers = next(p for p in dr.products if p.name == "managers")
    by_region: dict[object, set[str]] = {}
    for row in managers.sample:
        by_region.setdefault(row["region_ref"], set()).add(row["manager_name"])
    assert by_region, "no manager rows sampled"
    assert all(len(names) > 1 for names in by_region.values() if len(names) >= 1), (
        f"a region's own managers share one name: {by_region}"
    )
    # At least one region must actually have 2 sampled managers for the check above to
    # be meaningful (not vacuously true because every group happened to have 1 row).
    assert any(
        sum(1 for row in managers.sample if row["region_ref"] == region) >= 2 for region in by_region
    ), f"no region had >=2 sampled managers to compare: {by_region}"


def test_three_level_person_scoping_uses_three_distinct_variable_names() -> None:
    # The plan explicitly named this as what the first draft missed: a child <generate>
    # that itself contains a nested_list, both using person fields, alongside the
    # outermost generate also using one — three ancestor/descendant scopes deep. A
    # naming scheme with only two fixed names (rather than depth-based) would collide
    # here. Checked statically (variable declarations in the rendered XML), since the
    # bug is a render-time naming artifact, not something that needs a dry-run to see.
    spec = {"generates": [{
        "name": "companies", "count": 2, "target": "JSON",
        "fields": [{"name": "ceo", "kind": "person_name"}],
        "children": [{
            "name": "departments", "count": 2, "target": "JSON",
            "fields": [
                {"name": "director", "kind": "person_name"},
                {"name": "staff", "kind": "nested_list", "min": 2, "max": 2,
                 "fields": [{"name": "staff_name", "kind": "person_name"}]},
            ],
        }],
    }]}
    xml = render(spec)
    assert lint_source(xml).ok, xml
    var_names = re.findall(r'<variable name="(_ent_person\w*)" entity="Person"/>', xml)
    assert len(var_names) == 3, f"expected 3 person-variable declarations, got: {var_names}"
    assert len(set(var_names)) == 3, f"variable names collide, would shadow each other: {var_names}"


def test_constant_with_values_array_is_rejected_as_ambiguous() -> None:
    # Changing constant intent into values intent is a semantic repair, not normalization.
    spec = {"generates": [{"name": "x", "count": 3, "target": "JSON",
                           "fields": [{"name": "genre", "kind": "constant",
                                       "values": ["fiction", "nonfiction", "reference"]}]}]}
    with pytest.raises(ValueError, match="constant with values is ambiguous"):
        render(spec)


def test_weighted_with_scalar_value_is_rejected_as_ambiguous() -> None:
    # Splitting arbitrary text changes business values and therefore fails closed.
    spec = {"generates": [{"name": "x", "count": 3, "target": "JSON",
                           "fields": [{"name": "dish", "kind": "weighted",
                                       "value": "pizza/pasta/salad/soup",
                                       "weights": [2, 1, 1, 1]}]}]}
    with pytest.raises(ValueError, match="requires an explicit values array"):
        render(spec)


def test_weighted_with_script_list_literal_is_rejected_as_ambiguous() -> None:
    # A script is not reinterpreted as literal values by lossless normalization.
    spec = {"generates": [{"name": "x", "count": 3, "target": "JSON",
                           "fields": [{"name": "dish", "kind": "weighted",
                                       "script": "['pasta', 'pizza', 'salad']",
                                       "weights": [0.25, 0.5, 0.25]}]}]}
    with pytest.raises(ValueError, match="requires an explicit values array"):
        render(spec)


def test_script_kind_with_fake_unique_function_is_rejected() -> None:
    # Raw Python is never rewritten into a different field strategy.
    spec = {"generates": [{"name": "p", "count": 5, "target": "JSON",
                           "fields": [{"name": "seat", "kind": "script",
                                       "script": "random.unique(1, 20)"}]}]}
    with pytest.raises(ValueError, match="invented unique helper"):
        render(spec)


def test_duplicate_generate_names_are_rejected_without_dropping_intent() -> None:
    spec = {"generates": [
        {"name": "x", "count": 5, "target": "JSON", "fields": []},
        {"name": "x", "count": 5, "target": "JSON", "fields": [{"name": "id", "kind": "increment"}]},
    ]}
    with pytest.raises(ValueError, match="product names must be unique"):
        render(spec)


def test_duplicate_child_generate_names_are_rejected_without_dropping_intent() -> None:
    spec = {"generates": [{"name": "parent", "count": 2, "target": "JSON",
                           "fields": [{"name": "id", "kind": "increment"}],
                           "children": [
                               {"name": "child", "count": 1, "target": "JSON", "fields": []},
                               {"name": "child", "count": 1, "target": "JSON",
                                "fields": [{"name": "note", "kind": "constant", "value": "x"}]},
                           ]}]}
    with pytest.raises(ValueError, match="product names must be unique"):
        render(spec)


def test_nested_unique_in_nested_list_rejected_with_clear_message() -> None:
    # Verify that the scaffold use case rejects nested-unique and surfaces the error.

    spec = {"generates": [{"name": "flights", "count": 3, "target": "JSON",
                           "fields": [
                               {"name": "flight_no", "kind": "pattern", "pattern": "[A-Z]{2}[0-9]{4}"},
                               {"name": "passengers", "kind": "nested_list", "min": 2, "max": 2,
                                "fields": [{"name": "seat", "kind": "int_range", "min": 1, "max": 5,
                                            "unique": True}]},
                           ]}]}
    result = scaffold_spec(ScaffoldRequest(spec=spec))
    assert not result.ok
    assert result.stage is AuthoringStage.RENDER
    assert result.error is not None
    assert "unsupported feature" in result.error
    assert "unique" in result.error
    assert "seat" in result.error


def test_three_level_nesting_is_rejected_explicitly() -> None:
    # Three-level hierarchy (customers -> accounts -> transactions) is not supported
    # and must fail explicitly with a clear error naming the generates involved.
    spec = {"generates": [{"name": "customers", "count": 2, "target": "JSON",
                           "fields": [{"name": "id", "kind": "increment"}],
                           "children": [
                               {"name": "accounts", "count": 2, "target": "JSON",
                                "fields": [{"name": "account_id", "kind": "increment"}],
                                "children": [
                                    {"name": "transactions", "count": 2, "target": "JSON",
                                     "fields": [{"name": "tx_id", "kind": "increment"}]},
                                ]}
                           ]}]}
    with pytest.raises(ValueError, match="unsupported feature.*transactions.*nested more than one level"):
        render(spec)


def test_three_level_nesting_rejected_via_check() -> None:
    # Verify the service use case also properly rejects three-level nesting.

    spec = {"generates": [{"name": "customers", "count": 2, "target": "JSON",
                           "fields": [{"name": "id", "kind": "increment"}],
                           "children": [
                               {"name": "accounts", "count": 2, "target": "JSON",
                                "fields": [{"name": "account_id", "kind": "increment"}],
                                "children": [
                                    {"name": "transactions", "count": 2, "target": "JSON",
                                     "fields": [{"name": "tx_id", "kind": "increment"}]},
                                ]}
                           ]}]}
    result = scaffold_spec(ScaffoldRequest(spec=spec))
    assert not result.ok
    assert result.stage is AuthoringStage.RENDER
    assert result.error is not None
    assert "unsupported feature" in result.error
    assert "transactions" in result.error
    assert "nested more than one level" in result.error


def test_kind_alias_normalization_surfaces_as_note() -> None:
    # Near-miss recovery: a spec using kind="weighted_values" (alias for "weighted")
    # should normalize successfully and surface a normalization_notes entry on check()
    # result to document the repair — the spec is still valid and renders.
    spec = {"generates": [{"name": "dishes", "count": 10, "target": "JSON",
                           "fields": [{"name": "name", "kind": "weighted_values",
                                       "values": ["pasta", "pizza", "salad"],
                                       "weights": [2, 1, 1]}]}]}
    result = scaffold_spec(ScaffoldRequest(spec=spec, dry_run=False))
    assert result.ok
    assert result.stage is AuthoringStage.LINT
    assert len(result.normalization_notes) > 0
    # The note should mention the alias normalization
    assert any("weighted_values" in note and "weighted" in note for note in result.normalization_notes), (
        f"expected a normalization_notes entry about weighted_values→weighted, got: {result.normalization_notes}"
    )


def test_source_backed_unique_cardinality_propagation_insufficient() -> None:
    # Defect 1: source-backed unique ranges must have their cardinality verified against
    # the producer's count, not silently under-produce. This spec has a 5-row producer
    # and a reader with unique range 1..2 (grid too small) — must fail at render with
    # a message mentioning the producer.
    spec = {
        "generates": [
            {"name": "producer", "count": 5, "target": "mem,JSON",
             "fields": [{"name": "id", "kind": "increment"}]},
            {"name": "reader", "source": "mem", "source_type": "producer",
             "fields": [
                 {"name": "id", "kind": "script", "script": "id"},
                 {"name": "seat", "kind": "int_range", "min": 1, "max": 2, "unique": True},
             ]},
        ]
    }
    with pytest.raises(ValueError, match="unique"):
        render(spec)


def test_source_backed_unique_cardinality_propagation_sufficient() -> None:
    # Positive case: same producer (count=5) but unique range 1..10 (grid large enough)
    # — must render successfully, verifying cardinality propagation worked.
    spec = {
        "generates": [
            {"name": "producer", "count": 5, "target": "mem,JSON",
             "fields": [{"name": "id", "kind": "increment"}]},
            {"name": "reader", "source": "mem", "source_type": "producer",
             "fields": [
                 {"name": "id", "kind": "script", "script": "id"},
                 {"name": "seat", "kind": "int_range", "min": 1, "max": 10, "unique": True},
             ]},
        ]
    }
    xml = render(spec)
    assert lint_source(xml).ok, xml
    # Verify both generates rendered
    assert '<generate name="producer"' in xml
    assert '<generate name="reader"' in xml
    reader_open = next(line for line in xml.splitlines() if '<generate name="reader"' in line)
    assert "count=" not in reader_open


def test_source_backed_unique_rejects_unresolvable_file_cardinality() -> None:
    spec = {
        "generates": [
            {
                "name": "reader",
                "source": "external.csv",
                "fields": [
                    {"name": "seat", "kind": "int_range", "min": 1, "max": 10, "unique": True},
                ],
            }
        ]
    }

    with pytest.raises(ValueError, match="cardinality is not statically known"):
        render(spec)


def test_children_as_object_normalized_to_array() -> None:
    # Defect 2: if a model emits children as an object instead of an array,
    # it should be normalized to a one-item list with a note, not silently dropped.
    spec = {
        "generates": [
            {"name": "parent", "count": 2, "target": "JSON",
             "fields": [{"name": "id", "kind": "increment"}],
             "children": {
                 "name": "child", "count": 1,
                 "fields": [{"name": "parent_id", "kind": "script", "script": "parent.id"}],
             },
            }
        ]
    }
    result = scaffold_spec(ScaffoldRequest(spec=spec, dry_run=False))
    assert result.ok
    assert result.xml is not None
    # Verify the note about normalization is present
    assert any("object-shaped 'children of generate" in note for note in result.normalization_notes), (
        f"expected normalization note about children, got: {result.normalization_notes}"
    )
    # Verify child was rendered
    assert '<generate name="child"' in result.xml


def test_children_as_string_rejected() -> None:
    # If children is a string instead of an array of objects, reject explicitly.
    spec = {
        "generates": [
            {"name": "parent", "count": 2, "target": "JSON",
             "fields": [{"name": "id", "kind": "increment"}],
             "children": "invalid_string",
            }
        ]
    }
    with pytest.raises(ValueError, match="must be an array"):
        render(spec)


def test_object_shaped_grandchild_is_rejected() -> None:
    spec = {
        "generates": [
            {
                "name": "parent",
                "count": 2,
                "fields": [{"name": "id", "kind": "increment"}],
                "children": {
                    "name": "child",
                    "count": 1,
                    "fields": [{"name": "id", "kind": "increment"}],
                    "children": {
                        "name": "grandchild",
                        "count": 1,
                        "fields": [{"name": "id", "kind": "increment"}],
                    },
                },
            }
        ]
    }

    with pytest.raises(
        ValueError,
        match="unsupported feature.*grandchild.*nested more than one level",
    ):
        render(spec)


def test_object_shaped_nested_fields_are_normalized() -> None:
    spec = {
        "generates": [
            {
                "name": "departments",
                "count": 2,
                "fields": [
                    {
                        "name": "employees",
                        "kind": "nested_list",
                        "min": 1,
                        "max": 1,
                        "fields": {"name": "employee_id", "kind": "increment"},
                    }
                ],
            }
        ]
    }

    result = scaffold_spec(ScaffoldRequest(spec=spec, dry_run=False))

    assert result.ok
    assert result.xml is not None
    assert '<key name="employee_id" generator="IncrementGenerator"/>' in result.xml
    assert any("object-shaped 'nested fields" in note for note in result.normalization_notes)


def test_non_list_nested_fields_are_rejected() -> None:
    spec = {
        "generates": [
            {
                "name": "departments",
                "count": 2,
                "fields": [
                    {
                        "name": "employees",
                        "kind": "nested_list",
                        "fields": "not-an-array",
                    }
                ],
            }
        ]
    }

    with pytest.raises(ValueError, match="nested fields.*must be an array"):
        render(spec)


def test_deeper_object_shaped_nested_fields_are_rejected() -> None:
    spec = {
        "generates": [
            {
                "name": "departments",
                "count": 2,
                "fields": [
                    {
                        "name": "teams",
                        "kind": "nested_list",
                        "fields": {
                            "name": "members",
                            "kind": "nested_list",
                            "fields": {"name": "member_id", "kind": "increment"},
                        },
                    }
                ],
            }
        ]
    }

    with pytest.raises(ValueError, match="nested field 'members' more than one level deep"):
        render(spec)


def test_parent_with_no_fields_but_child_with_fields_valid() -> None:
    # Defect 3: a parent with no fields but a child with fields is valid DSL.
    # Previously only checked top-level generates for emptiness; must now check
    # recursively across all generates via _iter_generates.
    spec = {
        "generates": [
            {"name": "parent", "count": 2, "target": "JSON",
             "fields": [],
             "children": [
                 {"name": "child", "count": 1,
                  "fields": [{"name": "child_id", "kind": "increment"}]},
             ],
            }
        ]
    }
    xml = render(spec)
    assert lint_source(xml).ok, xml
    # Verify both parent and child were rendered
    assert '<generate name="parent"' in xml
    assert '<generate name="child"' in xml
    # Verify child has the field
    assert '<key name="child_id"' in xml
