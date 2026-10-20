# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""CE transaction facts and independent optional verification gates."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field, StrictBool, model_validator

from .common import AuthoringModel, NonEmptyStrictStr, NonNegativeStrictInt
from .expectations import ExpectationIntent


class IdentifierRole(AuthoringModel):
    """One field uniquely identifies rows across the complete product capture.

    A local sequence repeated under different parents is not a product identifier.
    Memstore readback proof requires exactly one producer identifier declaration.
    """

    kind: Literal["identifier"] = "identifier"


class ForeignKeyRole(AuthoringModel):
    """One field references a parent product's field; this is not a multi-column join.

    Nested lineage must copy the actual immediate parent's field. Memstore
    readback proof pairs one consumer role with the producer's identifier.
    """

    kind: Literal["foreign_key"] = "foreign_key"
    parent_product: NonEmptyStrictStr
    parent_field: NonEmptyStrictStr


class TimestampRole(AuthoringModel):
    kind: Literal["timestamp"] = "timestamp"


class ValueRole(AuthoringModel):
    kind: Literal["value"] = "value"


FieldRole = Annotated[IdentifierRole | ForeignKeyRole | TimestampRole | ValueRole, Field(discriminator="kind")]


class ProductRoleDeclaration(AuthoringModel):
    product: NonEmptyStrictStr
    field: NonEmptyStrictStr
    list_field: NonEmptyStrictStr | None = None
    role: FieldRole


class AcceptanceOrigin(StrEnum):
    MODEL = "model"
    CALLER = "caller"
    DERIVED = "derived"


class AcceptanceRequirement(AuthoringModel):
    expectation: ExpectationIntent
    origin: AcceptanceOrigin


class BuildVerificationOptions(AuthoringModel):
    smoke_export: StrictBool = False
    deterministic_replay: StrictBool = False


class VerificationGateStatus(StrEnum):
    NOT_REQUESTED = "not_requested"
    NOT_APPLICABLE = "not_applicable"
    BLOCKED = "blocked"
    FAILED = "failed"
    PASSED = "passed"


class VerificationGateEvidence(AuthoringModel):
    status: VerificationGateStatus = VerificationGateStatus.NOT_REQUESTED
    reason: NonEmptyStrictStr | None = None


class ReplayScope(StrEnum):
    """Typed scope compared by deterministic replay verification."""

    FULL_BOUNDED_CAPTURE = "full_bounded_capture"


class ReplayMismatchKind(StrEnum):
    """Machine-readable reasons why two bounded captures differ."""

    MISSING_PRODUCT = "missing_product"
    UNEXPECTED_PRODUCT = "unexpected_product"
    ROW_COUNT = "row_count"
    ROW_CONTENT = "row_content"


class SmokeExportEvidence(AuthoringModel):
    """Typed evidence from exporter testing over the first bounded capture."""

    status: VerificationGateStatus = VerificationGateStatus.NOT_REQUESTED
    applicable_exporters: NonNegativeStrictInt = 0
    attempted_exporters: NonNegativeStrictInt = 0
    failed_exporters: NonNegativeStrictInt = 0
    reason: str = "Smoke export was not requested"

    @model_validator(mode="after")
    def _consistent_counts(self) -> SmokeExportEvidence:
        if self.attempted_exporters > self.applicable_exporters:
            raise ValueError("attempted_exporters must not exceed applicable_exporters")
        if self.failed_exporters > self.attempted_exporters:
            raise ValueError("failed_exporters must not exceed attempted_exporters")
        return self


class ReplayProductMismatch(AuthoringModel):
    """Compact product-level difference between two full bounded captures."""

    product: NonEmptyStrictStr
    kind: ReplayMismatchKind
    first_count: NonNegativeStrictInt
    replay_count: NonNegativeStrictInt
    first_difference: NonNegativeStrictInt | None = None


class DeterministicReplayEvidence(AuthoringModel):
    """Typed result of an optional full bounded-capture replay comparison."""

    status: VerificationGateStatus = VerificationGateStatus.NOT_REQUESTED
    scope: ReplayScope = ReplayScope.FULL_BOUNDED_CAPTURE
    compared_products: NonNegativeStrictInt = 0
    compared_rows: NonNegativeStrictInt = 0
    mismatches: tuple[ReplayProductMismatch, ...] = ()
    reason: str = "Deterministic replay was not requested"


class BuildVerificationEvidence(AuthoringModel):
    smoke_export: SmokeExportEvidence = Field(default_factory=SmokeExportEvidence)
    deterministic_replay: DeterministicReplayEvidence = Field(default_factory=DeterministicReplayEvidence)

    @property
    def gates_passed(self) -> bool:
        return all(
            gate.status not in {VerificationGateStatus.BLOCKED, VerificationGateStatus.FAILED}
            for gate in (self.smoke_export, self.deterministic_replay)
        )
