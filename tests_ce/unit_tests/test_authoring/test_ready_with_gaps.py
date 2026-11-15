# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Coverage facts, their warnings and the ready_with_gaps outcome type (domain only)."""

from __future__ import annotations

from pathlib import PurePosixPath

import pytest
from pydantic import ValidationError

from datamimic_ce.authoring.domain.acceptance_contract import (
    AcceptanceCheckV1,
    AcceptanceProductV1,
    AcceptanceRelationshipV1,
    AcceptanceSpecV1,
    build_coverage,
)
from datamimic_ce.authoring.domain.build_rules import authoring_rule_catalog
from datamimic_ce.authoring.domain.capture import CaptureStatus, ProductCaptureEvidence
from datamimic_ce.authoring.domain.coverage import (
    BuildCoverage,
    CoverageGapKind,
    ProductCoverage,
    unread_data_files,
)
from datamimic_ce.authoring.domain.diagnostics import AuthoringRuleId, DiagnosticPhase
from datamimic_ce.authoring.domain.expectations import (
    DeclaredSinkIdentity,
    DeclaredSinkRowsSubject,
    ExactCountExpectation,
    PerParentCountExpectation,
    PerParentRowsSubject,
    ProductRowsSubject,
)
from datamimic_ce.authoring.domain.requests import (
    BuildArtifact,
    BuildAssurance,
    ProductEvidence,
    ProjectFileDigest,
    ReadyWithGapsBuild,
)

_DIGEST = "0" * 64
_SINK = DeclaredSinkIdentity(kind="database", environment="dev", entity="orders")


def _coverage(
    *,
    seeded: bool = True,
    unread: tuple[str, ...] = (),
    without: tuple[str, ...] = (),
    sinks: tuple[DeclaredSinkIdentity, ...] = (),
) -> BuildCoverage:
    return BuildCoverage(
        expectation_count=1,
        products=(ProductCoverage(product="customers", expectations=1),),
        products_without_expectation=without,
        unread_data_files=tuple(PurePosixPath(item) for item in unread),
        unchecked_declared_sinks=sinks,
        seeded=seeded,
    )


def _ready_fields(coverage: BuildCoverage) -> dict[str, object]:
    return {
        "artifact": BuildArtifact(
            files=(
                ProjectFileDigest(path=PurePosixPath("acceptance/build.json"), sha256=_DIGEST),
                ProjectFileDigest(path=PurePosixPath("datamimic.xml"), sha256=_DIGEST),
            ),
            ce_version="5.0.0-test",
        ),
        "assurance": BuildAssurance(mode="local_bounded"),
        "coverage": coverage,
        "evidence": (
            ProductEvidence(
                name="customers",
                count=2,
                capture=ProductCaptureEvidence(
                    status=CaptureStatus.COMPLETE, requested=2, observed=2, limit=10, reason="complete"
                ),
            ),
        ),
    }


def _product(name: str, *sinks: DeclaredSinkIdentity) -> AcceptanceProductV1:
    return AcceptanceProductV1(
        name=name, runtime_name=name, capture_name=name, count_per_invocation=2, declared_sinks=sinks
    )


def _check(expectation: ExactCountExpectation | PerParentCountExpectation) -> AcceptanceCheckV1:
    return AcceptanceCheckV1(expectation=expectation, path=("acceptance/build.json", "expectations", 0))


def test_an_open_gap_names_itself_in_declared_order_and_in_the_action_line() -> None:
    coverage = _coverage(seeded=False, unread=("data/a.csv",))

    assert coverage.has_gaps
    assert coverage.open_gaps == (CoverageGapKind.UNREAD_DATA_FILES, CoverageGapKind.SEEDED)
    assert coverage.action_required() == (
        "Ready with 2 open coverage gaps (unread_data_files, seeded). "
        "Do not report success until each gap is fixed or explained."
    )


def test_one_gap_uses_the_singular_and_no_gap_has_no_action() -> None:
    assert _coverage(unread=("data/a.csv",)).action_required() == (
        "Ready with 1 open coverage gap (unread_data_files). "
        "Do not report success until each gap is fixed or explained."
    )
    clean = _coverage()
    assert not clean.has_gaps
    assert clean.open_gaps == ()
    assert clean.action_required() is None
    assert clean.warnings() == ()


def test_each_gap_raises_one_coverage_gap_warning_with_counted_facts() -> None:
    coverage = _coverage(seeded=False, unread=("data/a.csv",), without=("shops",), sinks=(_SINK,))

    warnings = coverage.warnings()

    assert [item.path for item in warnings] == [
        ("coverage", "products_without_expectation"),
        ("coverage", "unread_data_files"),
        ("coverage", "unchecked_declared_sinks"),
        ("coverage", "seeded"),
    ]
    assert all(item.code == AuthoringRuleId.COVERAGE_GAP and item.severity == "warning" for item in warnings)
    assert all(item.phase is DiagnosticPhase.EVIDENCE for item in warnings)
    assert [item.actual for item in warnings] == [["shops"], ["data/a.csv"], ["database:dev:orders"], None]


def test_build_coverage_counts_expectations_for_each_product_and_names_unchecked_sinks() -> None:
    spec = AcceptanceSpecV1(
        products=(_product("cities"), _product("shops", _SINK), _product("orders")),
        relationships=(AcceptanceRelationshipV1(parent_product="cities", child_product="orders"),),
        checks=(
            _check(ExactCountExpectation(subject=ProductRowsSubject(product="cities"), count=2)),
            _check(
                PerParentCountExpectation(
                    subject=PerParentRowsSubject(parent_product="cities", child_product="orders"), count=2
                )
            ),
        ),
    )

    coverage = build_coverage(spec, seeded=True, unread_data_files=())

    assert coverage.expectation_count == 2
    assert {item.product: item.expectations for item in coverage.products} == {"cities": 1, "shops": 0, "orders": 1}
    assert coverage.products_without_expectation == ("shops",)
    assert coverage.unchecked_declared_sinks == (_SINK,)


def test_a_check_on_the_declared_sink_closes_the_sink_gap() -> None:
    spec = AcceptanceSpecV1(
        products=(_product("shops", _SINK),),
        checks=(_check(ExactCountExpectation(subject=DeclaredSinkRowsSubject(sink=_SINK), count=2)),),
    )

    coverage = build_coverage(spec, seeded=True, unread_data_files=())

    assert coverage.unchecked_declared_sinks == ()
    assert coverage.products_without_expectation == ("shops",)


def _paths(*names: str) -> tuple[PurePosixPath, ...]:
    return tuple(PurePosixPath(name) for name in names)


def test_only_unread_project_data_files_are_gaps() -> None:
    workspace = _paths(
        "datamimic.xml",
        "acceptance/build.json",
        "conf/data.csv",
        "docs/notes.csv",
        "lib/table.json",
        "data/deep/lib/table.csv",
        "data/README.txt",
        "data/regions.csv",
        "data/cities.csv",
        "data/orders.parquet",
        "scripts/helper.py",
    )

    unread = unread_data_files(workspace, read_paths=_paths("datamimic.xml"), parent_read=_paths("data/cities.csv"))

    assert unread == _paths("data/orders.parquet", "data/regions.csv")


def test_a_read_path_and_a_parent_read_path_both_close_the_gap() -> None:
    workspace = _paths("data/a.csv", "data/b.csv")

    assert unread_data_files(workspace, read_paths=_paths("data/a.csv"), parent_read=_paths("data/b.csv")) == ()


def test_the_outcome_type_refuses_a_coverage_without_gap_and_a_wrong_action() -> None:
    with pytest.raises(ValidationError, match="ready, not ready_with_gaps"):
        ReadyWithGapsBuild(action_required="x", **_ready_fields(_coverage()))
    with pytest.raises(ValidationError, match="action_required"):
        ReadyWithGapsBuild(action_required="wrong", **_ready_fields(_coverage(seeded=False)))


def test_the_outcome_type_accepts_the_action_that_its_coverage_states() -> None:
    coverage = _coverage(seeded=False)

    built = ReadyWithGapsBuild(action_required=coverage.action_required() or "", **_ready_fields(coverage))

    assert built.outcome == "ready_with_gaps"
    assert built.coverage.open_gaps == (CoverageGapKind.SEEDED,)


def test_the_outcome_type_keeps_the_ready_proof_checks() -> None:
    fields = _ready_fields(_coverage(seeded=False))
    fields["evidence"] = (ProductEvidence(name="customers", count=2),)

    with pytest.raises(ValidationError, match="capture provenance"):
        ReadyWithGapsBuild(action_required=_coverage(seeded=False).action_required() or "", **fields)


def test_both_new_rules_are_in_the_catalog_with_their_severity() -> None:
    by_id = {rule.rule_id: rule for rule in authoring_rule_catalog()}

    assert by_id[AuthoringRuleId.COVERAGE_GAP].severity == "warning"
    assert by_id[AuthoringRuleId.MISSING_EXPECTATION].severity == "error"
    assert AuthoringRuleId.COVERAGE_GAP.value == "coverage_gap"
    assert AuthoringRuleId.MISSING_EXPECTATION.value == "missing_expectation"
