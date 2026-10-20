"""Complete-capture acceptance controls for canonical DM JSON transactions."""

from decimal import Decimal

import pytest

from datamimic_ce.authoring.adapters.dm_json_codec import CeDmJsonCodec
from datamimic_ce.authoring.domain.acceptance_contract import AcceptanceProjectionError
from datamimic_ce.authoring.domain.acceptance_evaluation import evaluate_acceptance
from datamimic_ce.authoring.domain.capture import (
    CapturedProduct,
    CapturedProducts,
    CaptureStatus,
    ProductCaptureEvidence,
)
from datamimic_ce.authoring.domain.requests import BuildRequestV4
from datamimic_ce.authoring.projection.acceptance import project_acceptance


def project(xml, **kwargs):
    codec = CeDmJsonCodec()
    document = codec.compile(codec.decompile(xml)).document
    request = BuildRequestV4(document=document, **kwargs)
    return project_acceptance(request, document)


def capture(**products):
    return CapturedProducts(
        tuple(
            CapturedProduct(
                name,
                tuple(rows),
                ProductCaptureEvidence(
                    status=CaptureStatus.COMPLETE,
                    requested=len(rows),
                    observed=len(rows),
                    limit=100,
                    reason="Complete bounded capture",
                ),
            )
            for name, rows in products.items()
        ),
        max_count=100,
    )


def test_derived_counts_ranges_values_and_origin_are_never_omitted():
    spec = project(
        '<setup><generate name="rows" count="2"><key name="n" type="int" min="1" max="3"/><key name="state" values="&apos;a&apos;,&apos;b&apos;"/></generate></setup>'
    )
    assert {check.expectation.kind for check in spec.checks} == {"exact_count", "range", "allowed_values"}
    assert {check.origin for check in spec.checks} == {"derived"}
    assert not evaluate_acceptance(spec, capture(rows=[{"n": 1, "state": "a"}, {"n": 3, "state": "b"}]))
    failures = evaluate_acceptance(spec, capture(rows=[{"n": 5, "state": "c"}]))
    assert {failure.code for failure in failures} == {"exact_count", "range", "allowed_values"}


@pytest.mark.parametrize(
    "broken",
    [
        CapturedProducts((), 10),
        CapturedProducts((CapturedProduct("rows", ({"id": 1},)),), 10),
        CapturedProducts(
            (
                CapturedProduct(
                    "rows",
                    (1,),
                    ProductCaptureEvidence(
                        status=CaptureStatus.COMPLETE, requested=1, observed=1, limit=10, reason="complete"
                    ),
                ),
            ),
            10,
        ),
    ],
)
def test_missing_scalar_or_unproven_capture_fails_even_without_explicit_checks(broken):
    spec = project('<setup><generate name="rows" count="1"><key name="id" constant="1"/></generate></setup>')
    assert evaluate_acceptance(spec, broken)


def test_duplicate_capture_and_provenance_row_mismatch_fail():
    spec = project('<setup><generate name="rows" count="1"><key name="id" constant="1"/></generate></setup>')
    good = capture(rows=[{"id": 1}])
    assert evaluate_acceptance(spec, CapturedProducts(good.products * 2, 100))
    item = good.products[0]
    mismatch = evaluate_acceptance(spec, CapturedProducts((CapturedProduct(item.name, (), item.capture),), 100))
    # "complete" evidence that disagrees with its rows is a provenance failure, not a named incomplete status.
    assert mismatch[0].message == "Product capture is incomplete or its provenance is inconsistent."


def test_nested_parent_counts_use_real_join_not_matching_totals():
    spec = project(
        '<setup><generate name="parents" count="2"><key name="id" type="int" min="1" max="2"/><generate name="children" count="2"><key name="parent_id" script="parent.id"/></generate></generate></setup>'
    )
    assert not evaluate_acceptance(
        spec,
        capture(
            parents=[{"id": 1}, {"id": 2}],
            children=[{"parent_id": 1}, {"parent_id": 1}, {"parent_id": 2}, {"parent_id": 2}],
        ),
    )
    bad = evaluate_acceptance(spec, capture(parents=[{"id": 1}, {"id": 2}], children=[{"parent_id": 1}] * 4))
    assert any(item.code == "per_parent_count" for item in bad)


@pytest.mark.parametrize("subject", [{"product": "missing"}, {"product": "rows", "list_field": "missing"}])
def test_unknown_expectation_subject_has_structured_path(subject):
    with pytest.raises(AcceptanceProjectionError) as error:
        project(
            '<setup><generate name="rows" count="1"><key name="id" constant="1"/></generate></setup>',
            expectations=[{"kind": "exact_count", "subject": {"kind": "product", **subject}, "count": 1}],
        )
    assert error.value.diagnostics[0].path[:2] == ("expectations", 0)


def test_nested_list_checks_flatten_count_and_partition_unique():
    spec = project(
        '<setup><generate name="rows" count="2"><nestedKey name="items" type="list" count="2"><key name="id" type="int" min="1" max="2"/></nestedKey></generate></setup>',
        expectations=[
            {
                "kind": "exact_count",
                "subject": {"kind": "product", "product": "rows", "list_field": "items"},
                "count": 4,
            },
            {
                "kind": "unique",
                "subject": {"kind": "product", "product": "rows", "list_field": "items"},
                "field": "id",
                "scope": "per_parent",
            },
        ],
    )
    rows = [{"items": [{"id": 1}, {"id": 2}]}, {"items": [{"id": 1}, {"id": 2}]}]
    assert not evaluate_acceptance(spec, capture(rows=rows))
    rows[0]["items"][1]["id"] = 1
    assert any(item.code == "unique" for item in evaluate_acceptance(spec, capture(rows=rows)))


def test_memstore_readback_requires_explicit_identity_pair_and_equal_identity_sets():
    xml = '<setup><memstore id="store"/><generate name="parents" count="2" target="store"><key name="id" type="int" min="1" max="2"/></generate><generate name="copy" source="store" type="parents"><key name="id" script="this.id"/></generate></setup>'
    with pytest.raises(AcceptanceProjectionError):
        project(xml)
    roles = [
        {"product": "parents", "field": "id", "role": {"kind": "identifier"}},
        {
            "product": "copy",
            "field": "id",
            "role": {"kind": "foreign_key", "parent_product": "parents", "parent_field": "id"},
        },
    ]
    spec = project(xml, product_roles=roles)
    assert not evaluate_acceptance(spec, capture(parents=[{"id": 1}, {"id": 2}], copy=[{"id": 2}, {"id": 1}]))
    failures = evaluate_acceptance(spec, capture(parents=[{"id": 1}, {"id": 2}], copy=[{"id": 1}, {"id": 1}]))
    assert failures


def test_per_generate_capture_limits_allow_nested_totals_above_request_bound():
    spec = project(
        '<setup><generate name="parents" count="2"><key name="id" type="int" min="1" max="2"/><generate name="children" count="2"><key name="parent_id" script="parent.id"/></generate></generate></setup>'
    )
    observed = capture(parents=[{"id": 1}, {"id": 2}], children=[{"parent_id": 1}] * 2 + [{"parent_id": 2}] * 2)
    assert not evaluate_acceptance(spec, CapturedProducts(observed.products, max_count=2))


def test_time_series_count_uses_ce_window_multiplier_and_preserves_data_scalars():
    from datetime import date, datetime
    from decimal import Decimal
    from uuid import uuid4

    spec = project(
        '<setup><generate name="rows" start="2026-01-01T00:00:00" end="2026-01-01T04:00:00" interval="PT1H" count="2"><key name="timestamp" script="ts.now"/></generate></setup>'
    )
    observed = capture(
        rows=[
            {"timestamp": datetime(2026, 1, 1), "date": date(2026, 1, 1), "decimal": Decimal("1.5"), "uuid": uuid4()}
            for _ in range(8)
        ]
    )
    assert not evaluate_acceptance(spec, CapturedProducts(observed.products, max_count=2))


def test_capture_nonfinite_and_mixed_rows_fail_without_throwing():
    spec = project('<setup><generate name="rows" count="2"><key name="id" constant="1"/></generate></setup>')
    assert evaluate_acceptance(spec, capture(rows=[{"id": 1}, 3]))
    assert evaluate_acceptance(spec, capture(rows=[{"id": 1}, {"id": float("nan")}]))


def test_public_authoring_import_stays_runtime_free():
    import subprocess
    import sys

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import datamimic_ce.authoring; assert not any(name.startswith(('datamimic_ce.engine.runtime','datamimic_ce.engine.io','datamimic_ce.interfaces.mcp','datamimic_ee')) for name in sys.modules)",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_numeric_literal_vocabulary_keeps_types_and_reuses_ce_parser():
    from datamimic_ce.engine.dsl.vocabulary.value_literals import parse_literal_values

    assert parse_literal_values("1, '1'") == (1, "1")
    assert parse_literal_values("1") == (1,)
    spec = project('<setup><generate name="rows" count="1"><key name="id" values="1,2"/></generate></setup>')
    assert not evaluate_acceptance(spec, capture(rows=[{"id": 1}]))
    assert any(item.code == "allowed_values" for item in evaluate_acceptance(spec, capture(rows=[{"id": "1"}])))
    assert any(item.code == "allowed_values" for item in evaluate_acceptance(spec, capture(rows=[{"id": True}])))


def test_declared_sink_union_counts_and_uniqueness_use_all_contributors():
    xml = '<setup><database id="db"/><generate name="a" count="1" target="db" targetEntity="all_rows"><key name="id" type="int" min="1" max="2"/></generate><generate name="b" count="1" target="db" targetEntity="all_rows"><key name="id" type="int" min="1" max="2"/></generate></setup>'
    subject = {"kind": "declared_sink", "sink": {"kind": "database", "environment": "db", "entity": "all_rows"}}
    spec = project(
        xml,
        expectations=[
            {"kind": "exact_count", "subject": subject, "count": 2},
            {"kind": "unique", "subject": subject, "field": "id"},
        ],
    )
    assert not evaluate_acceptance(spec, capture(a=[{"id": 1}], b=[{"id": 2}]))
    assert any(item.code == "unique" for item in evaluate_acceptance(spec, capture(a=[{"id": 1}], b=[{"id": 1}])))
    assert evaluate_acceptance(spec, capture(a=[{"id": 1}]))


@pytest.mark.parametrize(
    "expectation,good,bad",
    [
        ({"kind": "fixed_value", "field": "id", "value": 1}, {"id": 1}, {"id": "1"}),
        ({"kind": "field_present", "field": "id"}, {"id": 1}, {}),
        ({"kind": "field_absent", "field": "secret"}, {"id": 1}, {"id": 1, "secret": "bad"}),
        ({"kind": "row_condition", "condition": "id > 0"}, {"id": 1}, {"id": 0}),
    ],
)
def test_remaining_expectation_families_fail_with_typed_codes(expectation, good, bad):
    spec = project(
        '<setup><generate name="rows" count="1"><key name="id" script="1"/></generate></setup>',
        expectations=[{**expectation, "subject": {"kind": "product", "product": "rows"}}],
    )
    assert not evaluate_acceptance(spec, capture(rows=[good]))
    assert any(item.code == expectation["kind"] for item in evaluate_acceptance(spec, capture(rows=[bad])))


def test_caller_and_model_requirements_preserve_origins_and_paths():
    requirement = {"kind": "exact_count", "subject": {"kind": "product", "product": "rows"}, "count": 2}
    spec = project(
        '<setup><generate name="rows" count="1"><key name="id" constant="1"/></generate></setup>',
        expectations=[requirement],
        acceptance_requirements=[{"expectation": requirement, "origin": "caller"}],
    )
    failures = evaluate_acceptance(spec, capture(rows=[{"id": 1}]))
    assert {item.path for item in failures} == {("expectations", 0), ("acceptance_requirements", 0, "expectation")}
    assert {item.origin for item in spec.checks} == {"model", "caller", "derived"}
    from datamimic_ce.authoring.domain.acceptance_contract import AcceptanceSpecV1

    assert AcceptanceSpecV1.model_validate_json(spec.model_dump_json()) == spec


def test_explicit_source_entity_memstore_binding_uses_canonical_key():
    xml = '<setup><memstore id="store"/><generate name="parents" count="1" target="store"><key name="id" constant="1"/></generate><generate name="copy" source="store" sourceEntity="parents"><key name="id" script="this.id"/></generate></setup>'
    roles = [
        {"product": "parents", "field": "id", "role": {"kind": "identifier"}},
        {
            "product": "copy",
            "field": "id",
            "role": {"kind": "foreign_key", "parent_product": "parents", "parent_field": "id"},
        },
    ]
    spec = project(xml, product_roles=roles)
    assert not evaluate_acceptance(spec, capture(parents=[{"id": 1}], copy=[{"id": 1}]))


@pytest.mark.parametrize(
    "expression,expected",
    [("None", None), ("'abc'", "abc"), ("{1,2}", {1, 2}), ("{0:'x',1:'y'}", {0: "x", 1: "y"}), ("True", (True,))],
)
def test_shared_literal_parser_preserves_existing_ce_literal_modes(expression, expected):
    from datamimic_ce.engine.dsl.vocabulary.value_literals import parse_literal_values

    assert parse_literal_values(expression) == expected


def test_parent_script_unknown_field_rejects_projection_with_logical_path():
    with pytest.raises(AcceptanceProjectionError) as error:
        project(
            '<setup><generate name="parents" count="1"><key name="id" constant="1"/><generate name="children" count="1"><key name="id" script="parent.missing"/></generate></generate></setup>'
        )
    assert error.value.diagnostics[0].path[:2] == ("document", "root")


def test_evaluator_rejects_invalid_complete_provenance_even_when_manually_mutated():
    spec = project('<setup><generate name="rows" count="1"><key name="id" constant="1"/></generate></setup>')
    product = capture(rows=[{"id": 1}]).products[0]
    broken = product.capture.model_copy(update={"requested": 2})
    assert evaluate_acceptance(spec, CapturedProducts((CapturedProduct("rows", product.rows, broken),), 100))


def test_nested_list_identifier_role_is_unique_per_root_row_with_decimal_values():
    from decimal import Decimal

    spec = project(
        '<setup><generate name="rows" count="2"><nestedKey name="items" type="list" count="2"><key name="id" type="int" min="1" max="2"/><key name="price" type="decimal" min="1.1" max="9.9"/></nestedKey></generate></setup>',
        product_roles=[{"product": "rows", "field": "id", "list_field": "items", "role": {"kind": "identifier"}}],
    )
    rows = [
        {"items": [{"id": 1, "price": Decimal("1.1")}, {"id": 2, "price": Decimal("9.9")}]},
        {"items": [{"id": 1, "price": Decimal("5.0")}, {"id": 2, "price": Decimal("2.1")}]},
    ]
    assert not evaluate_acceptance(spec, capture(rows=rows))
    rows[1]["items"][1]["id"] = 1
    assert any(item.code == "unique" for item in evaluate_acceptance(spec, capture(rows=rows)))


def test_nested_foreign_key_role_cannot_pass_by_randomly_matching_parent_keys():
    xml = '<setup><generate name="parents" count="1"><key name="id" constant="1"/><generate name="children" count="1"><key name="parent_id" constant="1"/></generate></generate></setup>'
    role = {
        "product": "children",
        "field": "parent_id",
        "role": {"kind": "foreign_key", "parent_product": "parents", "parent_field": "id"},
    }
    with pytest.raises(AcceptanceProjectionError) as error:
        project(xml, product_roles=[role])
    assert error.value.diagnostics[0].path == ("product_roles", 0)
    assert project(
        xml.replace('name="parent_id" constant="1"', 'name="parent_id" script="parent.id"'), product_roles=[role]
    )


def test_memstore_write_only_target_blocks_assurance():
    with pytest.raises(AcceptanceProjectionError) as error:
        project(
            '<setup><memstore id="store"/><generate name="rows" count="1" target="store"><key name="id" constant="1"/></generate></setup>'
        )
    assert error.value.diagnostics[0].path[-1] == "target"


def test_memstore_same_name_field_must_read_source_even_if_value_accidentally_matches():
    xml = '<setup><memstore id="store"/><generate name="parents" count="1" target="store"><key name="id" constant="1"/></generate><generate name="copy" source="store" sourceEntity="parents"><key name="id" constant="1"/></generate></setup>'
    roles = [
        {"product": "parents", "field": "id", "role": {"kind": "identifier"}},
        {
            "product": "copy",
            "field": "id",
            "role": {"kind": "foreign_key", "parent_product": "parents", "parent_field": "id"},
        },
    ]
    with pytest.raises(AcceptanceProjectionError):
        project(xml, product_roles=roles)
    assert project(
        xml.replace(
            '<key name="id" constant="1"/></generate></setup>', '<key name="id" script="id"/></generate></setup>'
        ),
        product_roles=roles,
    )


def test_deep_nested_capture_names_use_the_actual_exporter_convention():
    xml = '<setup><generate name="parents" count="1"><key name="id" constant="1"/><generate name="children" count="1"><key name="id" script="parent.id"/><generate name="grandchildren" count="1"><key name="parent_id" script="parent.id"/></generate></generate></generate></setup>'
    spec = project(xml)
    assert spec.products[2].capture_name == "children|grandchildren"
    assert not evaluate_acceptance(
        spec, capture(**{"parents": [{"id": 1}], "children": [{"id": 1}], "children|grandchildren": [{"parent_id": 1}]})
    )


def test_row_condition_unknown_static_field_rejects_before_execution():
    with pytest.raises(AcceptanceProjectionError) as error:
        project(
            '<setup><generate name="rows" count="1"><key name="id" constant="1"/></generate></setup>',
            expectations=[
                {"kind": "row_condition", "subject": {"kind": "product", "product": "rows"}, "condition": "missing > 0"}
            ],
        )
    assert error.value.diagnostics[0].path[:2] == ("expectations", 0)


@pytest.mark.parametrize("status", [CaptureStatus.CAPPED, CaptureStatus.UNKNOWN])
def test_partial_source_capture_blocks_even_passing_whole_product_checks(status):
    spec = project(
        '<setup><generate name="rows" source="rows.csv"><key name="id" script="this.id"/></generate></setup>',
        expectations=[
            {"kind": "allowed_values", "subject": {"kind": "product", "product": "rows"}, "field": "id", "values": [1]}
        ],
    )
    proof = ProductCaptureEvidence(status=status, requested=2, observed=1, limit=1, reason="bounded partial capture")
    assert evaluate_acceptance(spec, CapturedProducts((CapturedProduct("rows", ({"id": 1},), proof),), 1))


def test_exhausted_source_is_complete_without_inventing_a_declared_count():
    spec = project(
        '<setup><generate name="rows" source="rows.csv"><key name="id" script="this.id"/></generate></setup>',
        expectations=[
            {
                "kind": "allowed_values",
                "subject": {"kind": "product", "product": "rows"},
                "field": "id",
                "values": [1, 2],
            }
        ],
    )
    assert not any(check.expectation.kind == "exact_count" for check in spec.checks)
    proof = ProductCaptureEvidence(
        status=CaptureStatus.EXHAUSTED, requested=None, observed=2, limit=10, reason="source exhausted"
    )
    assert not evaluate_acceptance(
        spec, CapturedProducts((CapturedProduct("rows", ({"id": 1}, {"id": 2}), proof),), 10)
    )


@pytest.mark.parametrize("join", [None, 999])
def test_per_parent_no_join_or_orphan_never_passes_matching_global_totals(join):
    child = '<key name="parent_id" script="parent.id"/>' if join else '<key name="parent_id" constant="1"/>'
    spec = project(
        '<setup><generate name="parents" count="1"><key name="id" constant="1"/><generate name="children" count="1">'
        + child
        + "</generate></generate></setup>"
    )
    failures = evaluate_acceptance(spec, capture(parents=[{"id": 1}], children=[{"parent_id": join or 1}]))
    assert any(item.code == "per_parent_count" for item in failures)


def test_memstore_ambiguous_typed_identity_pair_rejects_before_execution():
    xml = '<setup><memstore id="store"/><generate name="parents" count="1" target="store"><key name="id" constant="1"/></generate><generate name="copy" source="store" type="parents"><key name="id" script="this.id"/><key name="id_again" script="this.id"/></generate></setup>'
    roles = [
        {"product": "parents", "field": "id", "role": {"kind": "identifier"}},
        *[
            {
                "product": "copy",
                "field": name,
                "role": {"kind": "foreign_key", "parent_product": "parents", "parent_field": "id"},
            }
            for name in ("id", "id_again")
        ],
    ]
    with pytest.raises(AcceptanceProjectionError):
        project(xml, product_roles=roles)


@pytest.mark.parametrize(
    "producer,consumer",
    [
        ([{"id": 1}, {"id": 1}], [{"id": 1}, {"id": 1}]),
        ([{"id": 1}, {"id": 2}], [{"id": 1}]),
        ([{"id": 1}, {"id": 2}], [{"id": 1}, {"id": 999}]),
    ],
)
def test_memstore_duplicate_count_and_orphan_failures_cannot_be_masked(producer, consumer):
    xml = '<setup><memstore id="store"/><generate name="parents" count="2" target="store"><key name="id" script="1"/></generate><generate name="copy" source="store" type="parents"><key name="id" script="this.id"/></generate></setup>'
    roles = [
        {"product": "parents", "field": "id", "role": {"kind": "identifier"}},
        {
            "product": "copy",
            "field": "id",
            "role": {"kind": "foreign_key", "parent_product": "parents", "parent_field": "id"},
        },
    ]
    spec = project(xml, product_roles=roles)
    assert evaluate_acceptance(spec, capture(parents=producer, copy=consumer))


def test_duplicate_explicit_expectations_reject_and_conflicting_checks_both_evaluate():
    from pydantic import ValidationError

    xml = '<setup><generate name="rows" count="1"><key name="id" constant="1"/></generate></setup>'
    one = {"kind": "exact_count", "subject": {"kind": "product", "product": "rows"}, "count": 2}
    with pytest.raises(ValidationError):
        project(xml, expectations=[one, one])
    spec = project(xml, expectations=[one, {**one, "count": 3}])
    failures = evaluate_acceptance(spec, capture(rows=[{"id": 1}]))
    assert len(failures) == 2
    assert {item.expected for item in failures} == {2, 3}


def test_dedup_never_invents_derived_origin_for_explicit_only_check():
    from datamimic_ce.authoring.domain.expectations import ProductRowsSubject, RowConditionExpectation

    document = CeDmJsonCodec().decompile(
        '<setup><generate name="rows" count="1"><key name="id" constant="1"/></generate></setup>'
    )
    condition = RowConditionExpectation(subject=ProductRowsSubject(product="rows"), condition="id > 0")
    request = BuildRequestV4(document=document).model_copy(update={"expectations": (condition, condition)})
    spec = project_acceptance(request, document)
    matching = [check for check in spec.checks if check.expectation.kind == "row_condition"]
    assert len(matching) == 1
    assert matching[0].origin.value == "model"


def test_serialized_acceptance_contract_rejects_unknown_sink_without_contributors():
    from pydantic import ValidationError

    from datamimic_ce.authoring.domain.acceptance_contract import AcceptanceSpecV1

    with pytest.raises(ValidationError):
        AcceptanceSpecV1.model_validate(
            {
                "products": [],
                "checks": [
                    {
                        "path": ["expectations", 0],
                        "expectation": {
                            "kind": "exact_count",
                            "subject": {
                                "kind": "declared_sink",
                                "sink": {"kind": "database", "environment": "db", "entity": "rows"},
                            },
                            "count": 0,
                        },
                    }
                ],
            }
        )


def test_acceptance_domain_imports_have_no_runtime_or_adapter_dependency():
    import ast
    from pathlib import Path

    import datamimic_ce.authoring.domain.acceptance_contract as contract
    import datamimic_ce.authoring.domain.acceptance_evaluation as evaluation

    forbidden = (
        "datamimic_ce.authoring.adapters",
        "datamimic_ce.authoring.application",
        "datamimic_ce.engine.runtime",
        "datamimic_ce.engine.io",
        "datamimic_ce.interfaces",
    )
    for module in (contract, evaluation):
        tree = ast.parse(Path(module.__file__).read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert not (node.module or "").startswith(forbidden)
            if isinstance(node, ast.Import):
                assert not any(alias.name.startswith(forbidden) for alias in node.names)


@pytest.mark.parametrize("count,expected_minimum", [(15, 15), (1000, 1000), (1001, None)])
def test_capped_count_retry_uses_one_canonical_limit(count, expected_minimum):
    spec = project(f'<setup><generate name="rows" count="{count}"><key name="id" constant="1"/></generate></setup>')
    proof = ProductCaptureEvidence(
        status=CaptureStatus.CAPPED, requested=count, observed=10, limit=10, reason="bounded"
    )
    failures = evaluate_acceptance(
        spec, CapturedProducts((CapturedProduct("rows", tuple({"id": 1} for _ in range(10)), proof),), 10)
    )
    retries = [
        item.expected
        for item in failures
        if isinstance(item.expected, dict) and item.expected.get("parameter") == "max_count"
    ]
    assert len(retries) == (0 if expected_minimum is None else 1)
    if retries:
        assert retries[0]["minimum_value"] == expected_minimum
        assert retries[0]["affected_products"] == ["rows"]


def test_nested_and_time_series_retry_use_invocation_counts_not_total_rows():
    nested = project(
        '<setup><generate name="parents" count="2"><key name="id" constant="1"/><generate name="children" count="3"><key name="id" script="parent.id"/></generate></generate></setup>'
    )
    parents = capture(parents=[{"id": 1}, {"id": 2}]).products[0]
    proof = ProductCaptureEvidence(
        status=CaptureStatus.CAPPED, requested=6, observed=4, limit=4, reason="2 rows per invocation"
    )
    failures = evaluate_acceptance(
        nested, CapturedProducts((parents, CapturedProduct("children", tuple({"id": 1} for _ in range(4)), proof)), 2)
    )
    assert failures[0].expected["minimum_value"] == 3
    series = project(
        '<setup><generate name="rows" count="20" start="2026-01-01T00:00:00" end="2026-01-01T02:00:00" interval="PT1H"><key name="at" script="ts.now"/></generate></setup>'
    )
    proof = ProductCaptureEvidence(
        status=CaptureStatus.CAPPED, requested=40, observed=20, limit=20, reason="10 series cap"
    )
    failures = evaluate_acceptance(
        series, CapturedProducts((CapturedProduct("rows", tuple({"at": 1} for _ in range(20)), proof),), 10)
    )
    assert failures[0].expected["minimum_value"] == 20


def test_count_free_source_does_not_invent_retry_minimum_from_global_observations():
    spec = project(
        '<setup><generate name="rows" source="rows.csv"><key name="id" script="this.id"/></generate></setup>'
    )
    proof = ProductCaptureEvidence(
        status=CaptureStatus.CAPPED, requested=30, observed=10, limit=10, reason="bounded source"
    )
    failures = evaluate_acceptance(
        spec, CapturedProducts((CapturedProduct("rows", tuple({"id": 1} for _ in range(10)), proof),), 10)
    )
    assert failures and all(item.expected is None for item in failures)


def test_declared_nested_foreign_key_selects_join_over_unmarked_parent_copies():
    xml = (
        '<setup><generate name="parents" count="2">'
        '<key name="id" type="int" min="1" max="2"/><key name="label" constant="A"/>'
        '<generate name="children" count="2"><key name="parent_id" script="parent.id"/>'
        '<key name="parent_label" script="parent.label"/></generate></generate></setup>'
    )
    role = {
        "product": "children",
        "field": "parent_id",
        "role": {"kind": "foreign_key", "parent_product": "parents", "parent_field": "id"},
    }
    spec = project(xml, product_roles=[role])
    observed = capture(
        parents=[{"id": 1, "label": "A"}, {"id": 2, "label": "A"}],
        children=[{"parent_id": key, "parent_label": "A"} for key in (1, 1, 2, 2)],
    )
    assert not evaluate_acceptance(spec, observed)
    assert [(join.child_field, join.parent_field) for join in spec.relationships[0].joins] == [("parent_id", "id")]
    wrong_group = capture(
        parents=[{"id": 1, "label": "A"}, {"id": 2, "label": "A"}],
        children=[{"parent_id": 1, "parent_label": "A"}] * 4,
    )
    assert any(issue.code == "per_parent_count" for issue in evaluate_acceptance(spec, wrong_group))

    ambiguous = project(
        xml,
        product_roles=[
            role,
            {
                "product": "children",
                "field": "parent_label",
                "role": {"kind": "foreign_key", "parent_product": "parents", "parent_field": "label"},
            },
        ],
    )
    assert len(ambiguous.relationships[0].joins) == 2
    assert any(issue.code == "per_parent_count" for issue in evaluate_acceptance(ambiguous, observed))


@pytest.mark.parametrize(
    "left,right",
    [
        ({"amount": Decimal("1.2")}, {"amount": "1.2"}),
        ({"items": (1, 2)}, {"items": [1, 2]}),
        ({"value": True}, {"value": 1}),
    ],
)
def test_uniqueness_preserves_nested_native_types(left, right):
    spec = project(
        '<setup><generate name="rows" count="2"><key name="payload" script="{}"/></generate></setup>',
        expectations=[{"kind": "unique", "subject": {"kind": "product", "product": "rows"}, "field": "payload"}],
    )
    assert not evaluate_acceptance(spec, capture(rows=[{"payload": left}, {"payload": right}]))


def test_mapping_order_does_not_change_acceptance_identity():
    spec = project(
        '<setup><generate name="rows" count="2"><key name="payload" script="{}"/></generate></setup>',
        expectations=[{"kind": "unique", "subject": {"kind": "product", "product": "rows"}, "field": "payload"}],
    )
    failures = evaluate_acceptance(
        spec,
        capture(
            rows=[
                {"payload": {"a": {"b": 1}, "c": 2}},
                {"payload": {"c": 2, "a": {"b": 1}}},
            ]
        ),
    )
    assert [item.code for item in failures] == ["unique"]


def test_foreign_key_does_not_match_nested_decimal_to_string():
    from decimal import Decimal

    spec = project(
        '<setup><generate name="parents" count="1"><key name="id" script="{}"/></generate>'
        '<generate name="children" count="1"><key name="parent_id" script="{}"/></generate></setup>',
        expectations=[
            {
                "kind": "foreign_key",
                "parent": {"subject": {"kind": "product", "product": "parents"}, "field": "id"},
                "child": {"subject": {"kind": "product", "product": "children"}, "field": "parent_id"},
            }
        ],
    )
    failures = evaluate_acceptance(
        spec,
        capture(
            parents=[{"id": {"amount": Decimal("1.2")}}],
            children=[{"parent_id": {"amount": "1.2"}}],
        ),
    )
    assert [item.code for item in failures] == ["foreign_key"]


def test_memstore_alias_does_not_hide_ambiguous_producers():
    with pytest.raises(AcceptanceProjectionError, match="producer"):
        project(
            '<setup><memstore id="store"/>'
            '<generate name="a" type="shared" count="1" target="store"><key name="id" constant="1"/></generate>'
            '<generate name="b" targetEntity="shared" count="1" target="store"><key name="id" constant="2"/></generate>'
            '<generate name="copy" source="store" sourceEntity="shared">'
            '<key name="id" script="this.id"/></generate></setup>'
        )


def test_mutually_exclusive_branches_share_output_fields():
    spec = project(
        '<setup><generate name="rows" count="3"><condition>'
        '<if condition="True"><key name="code" constant="a"/></if>'
        '<else-if condition="False"><key name="code" constant="b"/><key name="extra" constant="x"/></else-if>'
        '<else><key name="code" constant="c"/></else>'
        '</condition></generate></setup>'
    )
    assert spec.products[0].fields == ("code", "extra")


@pytest.mark.parametrize(
    "fields",
    [
        '<key name="code" constant="a"/><key name="code" constant="b"/>',
        '<condition><if condition="True"><key name="code" constant="a"/>'
        '<key name="code" constant="b"/></if><else><key name="code" constant="c"/></else></condition>',
        '<key name="code" constant="a"/><condition><if condition="True">'
        '<key name="code" constant="b"/></if></condition>',
        '<condition><if condition="True"><key name="code" constant="a"/></if></condition>'
        '<condition><if condition="True"><key name="code" constant="b"/></if></condition>',
    ],
    ids=["same_scope", "same_branch", "outside_branch", "separate_conditions"],
)
def test_fields_on_the_same_execution_path_still_reject_duplicates(fields):
    with pytest.raises(AcceptanceProjectionError):
        project(f'<setup><generate name="rows" count="1">{fields}</generate></setup>')
