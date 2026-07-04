# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""The scaffold renderer must ALWAYS emit structurally-valid, dry-runnable DSL —
that is the whole point (a weak model chooses values, never touches XML)."""

import pytest

from datamimic_ce.authoring import lint_source
from datamimic_ce.authoring.dryrun import dry_run_source
from datamimic_ce.authoring.scaffold import render

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


def test_unknown_kind_degrades_to_valid_constant() -> None:
    # A model emitting an out-of-enum kind must still yield valid XML, not a crash.
    xml = render({"generates": [{"name": "g", "count": 2, "target": "JSON",
                                 "fields": [{"name": "f", "kind": "totally_made_up", "value": "x"}]}]})
    assert lint_source(xml).ok
