# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Shared domain fixtures for Build coverage and ready results."""

from pathlib import PurePosixPath

from datamimic_ce.authoring.domain.capture import CaptureStatus, ProductCaptureEvidence
from datamimic_ce.authoring.domain.coverage import (
    BuildCoverage,
    ExpectationResult,
    ListedExpectation,
    ListedExpectations,
    ProductCoverage,
)
from datamimic_ce.authoring.domain.expectations import DeclaredSinkIdentity, ExpectationIntentKind, ProductRowsSubject
from datamimic_ce.authoring.domain.proof import AcceptanceOrigin
from datamimic_ce.authoring.domain.requests import BuildArtifact, BuildAssurance, ProductEvidence, ProjectFileDigest


def coverage(
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


def ready_fields(coverage: BuildCoverage) -> dict[str, object]:
    return {
        "artifact": BuildArtifact(
            files=(
                ProjectFileDigest(path=PurePosixPath("acceptance/build.json"), sha256="0" * 64),
                ProjectFileDigest(path=PurePosixPath("datamimic.xml"), sha256="0" * 64),
            ),
            ce_version="5.0.0-test",
        ),
        "assurance": BuildAssurance(mode="local_bounded"),
        "coverage": coverage,
        "expectations": ListedExpectations(
            total=1,
            truncated=False,
            items=(
                ListedExpectation(
                    origin=AcceptanceOrigin.MODEL,
                    kind=ExpectationIntentKind.EXACT_COUNT,
                    subject=ProductRowsSubject(product="customers"),
                    field=None,
                    result=ExpectationResult.PASSED,
                ),
            ),
        ),
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
