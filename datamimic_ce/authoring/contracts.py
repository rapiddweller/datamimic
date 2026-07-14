# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Canonical contracts and input limits for agent-facing authoring operations.

Single source of truth across MCP, CLI, and internal service layers.  Keeping
the shared numeric limits here prevents one transport from accepting requests
that another transport rejects.
"""

from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Annotated, Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, JsonValue, StrictStr, model_validator

from datamimic_ce.authoring.diagnostics import Diagnostic, LintResult
from datamimic_ce.authoring.spec import (
    FieldIntentKind,
    LeafFieldKind,
    NonEmptyStrictStr,
    NonNegativeStrictInt,
    PositiveStrictInt,
    RegisteredFileExporterName,
    RuntimeFileSourcePath,
    RuntimeMemstoreSourceId,
)

MIN_DIAGNOSTICS = 1
MAX_DIAGNOSTICS = 200
MIN_DRY_RUN_COUNT = 1
MAX_DRY_RUN_COUNT = 1000
MIN_SAMPLE_ROWS = 1
MAX_SAMPLE_ROWS = 50
MIN_TIMEOUT_SECONDS = 1
MAX_TIMEOUT_SECONDS = 120


class AuthoringStage(StrEnum):
    """Canonical lifecycle stages for all authoring application results."""

    RUN = "run"
    LINT = "lint"
    RENDER = "render"
    DRY_RUN = "dry_run"
    ACCEPTANCE = "acceptance"
    VERIFICATION = "verification"


class AuthoringResponseFormat(StrEnum):
    """Canonical diagnostic projection requested by an authoring transport."""

    CONCISE = "concise"
    DETAILED = "detailed"


class VerificationGateStatus(StrEnum):
    """Stable outcome vocabulary for optional scaffold verification gates."""

    NOT_REQUESTED = "not_requested"
    BLOCKED = "blocked"
    PASSED = "passed"
    FAILED = "failed"
    NOT_APPLICABLE = "not_applicable"


class ReplayScope(StrEnum):
    """Typed scope compared by deterministic replay verification."""

    FULL_BOUNDED_CAPTURE = "full_bounded_capture"


class ReplayMismatchKind(StrEnum):
    """Machine-readable reasons why two bounded captures differ."""

    MISSING_PRODUCT = "missing_product"
    UNEXPECTED_PRODUCT = "unexpected_product"
    ROW_COUNT = "row_count"
    ROW_CONTENT = "row_content"


class ScaffoldVerification(BaseModel):
    """Optional gates executed as part of the canonical scaffold transaction."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    smoke_export: Annotated[
        bool,
        Field(
            description=(
            "Test applicable file exporters against rows from the canonical bounded run "
            "without performing another engine run"
            )
        ),
    ] = False
    deterministic_replay: Annotated[
        bool,
        Field(
            description=(
            "Run the same seeded bounded model once more and compare all bounded captured rows"
            )
        ),
    ] = False


class SmokeExportEvidence(BaseModel):
    """Typed evidence from exporter testing over the first bounded capture."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    status: VerificationGateStatus = VerificationGateStatus.NOT_REQUESTED
    applicable_exporters: NonNegativeStrictInt = 0
    attempted_exporters: NonNegativeStrictInt = 0
    failed_exporters: NonNegativeStrictInt = 0
    reason: str = "Smoke export was not requested"

    @model_validator(mode="after")
    def _consistent_counts(self) -> Self:
        if self.attempted_exporters > self.applicable_exporters:
            raise ValueError("attempted_exporters must not exceed applicable_exporters")
        if self.failed_exporters > self.attempted_exporters:
            raise ValueError("failed_exporters must not exceed attempted_exporters")
        return self


class ReplayProductMismatch(BaseModel):
    """Compact product-level difference between two full bounded captures."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    product: NonEmptyStrictStr
    kind: ReplayMismatchKind
    first_count: NonNegativeStrictInt
    replay_count: NonNegativeStrictInt
    first_difference: NonNegativeStrictInt | None = None


class DeterministicReplayEvidence(BaseModel):
    """Typed result of an optional full bounded-capture replay comparison."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    status: VerificationGateStatus = VerificationGateStatus.NOT_REQUESTED
    scope: ReplayScope = ReplayScope.FULL_BOUNDED_CAPTURE
    compared_products: NonNegativeStrictInt = 0
    compared_rows: NonNegativeStrictInt = 0
    mismatches: tuple[ReplayProductMismatch, ...] = ()
    reason: str = "Deterministic replay was not requested"


def _default_smoke_export_evidence() -> SmokeExportEvidence:
    return SmokeExportEvidence()


def _default_replay_evidence() -> DeterministicReplayEvidence:
    return DeterministicReplayEvidence()


class ScaffoldVerificationEvidence(BaseModel):
    """Canonical optional-gate evidence returned by every scaffold request."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    smoke_export: SmokeExportEvidence = Field(
        default_factory=_default_smoke_export_evidence
    )
    deterministic_replay: DeterministicReplayEvidence = Field(
        default_factory=_default_replay_evidence
    )

    @property
    def gates_passed(self) -> bool:
        """Whether all requested gates passed or had no applicable target."""

        passing = (
            VerificationGateStatus.NOT_REQUESTED,
            VerificationGateStatus.NOT_APPLICABLE,
            VerificationGateStatus.PASSED,
        )
        return (
            self.smoke_export.status in passing
            and self.deterministic_replay.status in passing
        )


def _default_scaffold_verification() -> ScaffoldVerification:
    return ScaffoldVerification()


class IntentValidationIssueCode(StrEnum):
    """Stable public classifications for invalid authoring intent."""

    UNKNOWN_FIELD = "unknown_field"
    MISSING_FIELD = "missing_field"
    INVALID_DISCRIMINATOR = "invalid_discriminator"
    INVALID_VALUE = "invalid_value"
    CONSTRAINT_VIOLATION = "constraint_violation"
    UNSUPPORTED_INTENT = "unsupported_intent"


class IntentValidationIssue(BaseModel):
    """One repair-oriented root cause from intent validation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    path: tuple[str | int, ...]
    code: IntentValidationIssueCode
    message: str = Field(min_length=1)
    allowed_fields: tuple[str, ...] = ()
    expected_fragment: dict[str, JsonValue] | None = None

    def summary(self) -> str:
        """Render the compatibility summary from this canonical issue."""

        location = ".".join(str(part) for part in self.path) or "spec"
        return f"{location}: {self.message}"


class CaptureStatus(StrEnum):
    """Runtime knowledge about whether a bounded product capture is complete."""

    COMPLETE = "complete"
    CAPPED = "capped"
    EXHAUSTED = "exhausted"
    UNKNOWN = "unknown"


class ProductCaptureEvidence(BaseModel):
    """Typed runtime evidence for one captured product."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    status: CaptureStatus
    requested: NonNegativeStrictInt | None
    observed: NonNegativeStrictInt
    limit: PositiveStrictInt
    reason: NonEmptyStrictStr

    @property
    def complete(self) -> bool:
        """Whether runtime evidence proves the bounded capture is complete."""

        return self.status in (CaptureStatus.COMPLETE, CaptureStatus.EXHAUSTED)

    @model_validator(mode="after")
    def _consistent_counts(self) -> "ProductCaptureEvidence":
        if self.observed > self.limit:
            raise ValueError("observed must not exceed limit")
        if (
            self.requested is not None
            and self.status is CaptureStatus.COMPLETE
            and self.observed != self.requested
        ):
            raise ValueError("complete capture must observe the requested count")
        if self.status is CaptureStatus.CAPPED and self.observed != self.limit:
            raise ValueError("capped capture must observe its limit")
        return self


class CheckRequest(BaseModel):
    """Canonical request contract for descriptor linting."""

    xml: str | None = Field(None, description="Inline descriptor XML (preferred for agents)")
    path: str | None = Field(
        None,
        description="Path to a descriptor file on the server's filesystem",
    )
    response_format: AuthoringResponseFormat = AuthoringResponseFormat.CONCISE
    max_diagnostics: int = Field(
        50,
        ge=MIN_DIAGNOSTICS,
        le=MAX_DIAGNOSTICS,
    )

    @model_validator(mode="after")
    def _exactly_one_input(self) -> "CheckRequest":
        if (self.xml is None) == (self.path is None):
            raise ValueError("Provide exactly one of 'xml' (inline descriptor) or 'path' (file)")
        return self


CheckResult = LintResult
"""Canonical response contract for descriptor linting."""


class RunRequest(BaseModel):
    """Canonical request contract for safe descriptor dry-runs."""

    xml: str | None = Field(None, description="Inline descriptor XML (preferred for agents)")
    path: str | None = Field(
        None,
        description="Path to a descriptor file on the server's filesystem",
    )
    sample_rows: int = Field(5, ge=MIN_SAMPLE_ROWS, le=MAX_SAMPLE_ROWS)
    max_count: int = Field(
        10,
        ge=MIN_DRY_RUN_COUNT,
        le=MAX_DRY_RUN_COUNT,
        description="Per-invocation record cap for every <generate> level",
    )
    allow_side_effects: bool = Field(
        False,
        description="Keep file/DB targets and allow <execute> (default: neutralized)",
    )
    smoke_export: bool = Field(
        False,
        description=(
            "Also push captured rows through the stripped FILE exporters in a temp dir "
            "(no artifacts) to catch export-time serialization crashes"
        ),
    )
    timeout_seconds: int = Field(
        30,
        ge=MIN_TIMEOUT_SECONDS,
        le=MAX_TIMEOUT_SECONDS,
    )
    response_format: AuthoringResponseFormat = AuthoringResponseFormat.CONCISE

    @model_validator(mode="after")
    def _exactly_one_input(self) -> "RunRequest":
        if (self.xml is None) == (self.path is None):
            raise ValueError("Provide exactly one of 'xml' (inline descriptor) or 'path' (file)")
        return self


class ScaffoldRequest(BaseModel):
    """Canonical request for complete compile, lint, run and acceptance verification."""

    model_config = ConfigDict(extra="forbid")

    spec: dict[str, Any] = Field(
        ...,
        description=(
            "Versioned AuthoringSpecV1 model.dm.json intent. The historical compact "
            "{'seed': ..., 'generates': [...]} shape is accepted through lossless "
            "normalization with visible notes."
        ),
    )
    max_count: int = Field(
        10,
        ge=MIN_DRY_RUN_COUNT,
        le=MAX_DRY_RUN_COUNT,
        description="Per-<generate> record cap for the bounded run (including nested generates)",
    )
    sample_rows: int = Field(
        5,
        ge=MIN_SAMPLE_ROWS,
        le=MAX_SAMPLE_ROWS,
        description="Sample rows to capture per product during dry-run",
    )
    response_format: AuthoringResponseFormat = Field(
        AuthoringResponseFormat.CONCISE,
        description="Response format: concise (key diagnostics) or detailed (full diagnostic info)",
    )
    verification: ScaffoldVerification = Field(
        default_factory=_default_scaffold_verification
    )


class ProductResult(BaseModel):
    """Result for a single product (generate output)."""

    name: str
    count: int
    sample: list[dict[str, Any]] = Field(default_factory=list)
    truncated_rows: bool = False
    capture: ProductCaptureEvidence


class CompilePlanModel(BaseModel):
    """Strict immutable base for compiler-owned handoff contracts."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        validate_default=True,
    )


class IdentifierRolePlan(CompilePlanModel):
    kind: Literal["identifier"] = "identifier"


class ForeignKeyRolePlan(CompilePlanModel):
    kind: Literal["foreign_key"] = "foreign_key"
    parent_product: NonEmptyStrictStr
    parent_field: NonEmptyStrictStr


class TimestampRolePlan(CompilePlanModel):
    kind: Literal["timestamp"] = "timestamp"


class ValueRolePlan(CompilePlanModel):
    kind: Literal["value"] = "value"


FieldRolePlan = Annotated[
    IdentifierRolePlan | ForeignKeyRolePlan | TimestampRolePlan | ValueRolePlan,
    Field(discriminator="kind"),
]


class LeafFieldPlan(CompilePlanModel):
    """Compiled leaf field; list-cardinality state is impossible here."""

    name: NonEmptyStrictStr
    kind: LeafFieldKind
    roles: list[FieldRolePlan] = Field(default_factory=list)


class NestedListFieldPlan(CompilePlanModel):
    """Compiled nested-list field with its required cardinality bounds."""

    name: NonEmptyStrictStr
    kind: Literal[FieldIntentKind.NESTED_LIST] = FieldIntentKind.NESTED_LIST
    roles: list[FieldRolePlan] = Field(default_factory=list)
    minimum_count: NonNegativeStrictInt
    maximum_count: NonNegativeStrictInt

    @model_validator(mode="after")
    def _ordered_counts(self) -> "NestedListFieldPlan":
        if self.minimum_count > self.maximum_count:
            raise ValueError("minimum_count must not exceed maximum_count")
        return self


FieldPlan = Annotated[LeafFieldPlan | NestedListFieldPlan, Field(discriminator="kind")]


class FileSourceBindingPlan(CompilePlanModel):
    kind: Literal["file"] = "file"
    path: RuntimeFileSourcePath
    separator: StrictStr | None = None
    distribution: Literal["ordered"] = "ordered"


class MemstoreSourceBindingPlan(CompilePlanModel):
    kind: Literal["memstore"] = "memstore"
    id: RuntimeMemstoreSourceId
    product: NonEmptyStrictStr | None = None
    distribution: Literal["ordered"] = "ordered"


SourceBindingPlan = Annotated[
    FileSourceBindingPlan | MemstoreSourceBindingPlan,
    Field(discriminator="kind"),
]


class FileTargetBindingPlan(CompilePlanModel):
    kind: Literal["file_export"] = "file_export"
    format: RegisteredFileExporterName
    export_uri: NonEmptyStrictStr | None = None


class MemstoreTargetBindingPlan(CompilePlanModel):
    kind: Literal["memstore"] = "memstore"
    id: NonEmptyStrictStr


TargetBindingPlan = Annotated[
    FileTargetBindingPlan | MemstoreTargetBindingPlan,
    Field(discriminator="kind"),
]


class ProductCompilePlanBase(CompilePlanModel):
    name: NonEmptyStrictStr
    fields: list[FieldPlan] = Field(default_factory=list)
    targets: list[TargetBindingPlan] = Field(default_factory=list)


class GeneratedProductCompilePlan(ProductCompilePlanBase):
    kind: Literal["generated"] = "generated"
    parent: NonEmptyStrictStr | None = None
    children: list[NonEmptyStrictStr] = Field(default_factory=list)
    static_count: PositiveStrictInt
    count_per_parent: PositiveStrictInt | None = None

    @model_validator(mode="after")
    def _valid_generation_scope(self) -> "GeneratedProductCompilePlan":
        if (self.parent is None) != (self.count_per_parent is None):
            raise ValueError("nested generated products require parent and count_per_parent together")
        if self.parent is not None and self.children:
            raise ValueError("nested generated products cannot own child products in V1")
        if not self.fields and not self.children:
            raise ValueError("generated product needs fields or child products")
        if len(self.children) != len(set(self.children)):
            raise ValueError("generated product child names must be unique")
        return self


class SourceProductCompilePlan(ProductCompilePlanBase):
    kind: Literal["source"] = "source"
    fields: list[FieldPlan] = Field(min_length=1)
    static_count: NonNegativeStrictInt | None
    source: SourceBindingPlan


class TimeSeriesProductCompilePlan(ProductCompilePlanBase):
    kind: Literal["time_series"] = "time_series"
    fields: list[FieldPlan] = Field(min_length=1)
    static_count: PositiveStrictInt
    series_count: PositiveStrictInt


ProductCompilePlan = Annotated[
    GeneratedProductCompilePlan | SourceProductCompilePlan | TimeSeriesProductCompilePlan,
    Field(discriminator="kind"),
]


class NestedRelationshipPlan(CompilePlanModel):
    kind: Literal["nested"] = "nested"
    parent: NonEmptyStrictStr
    child: NonEmptyStrictStr

    @model_validator(mode="after")
    def _different_products(self) -> "NestedRelationshipPlan":
        if self.parent == self.child:
            raise ValueError("relationship parent and child must differ")
        return self


class MemstoreRelationshipPlan(CompilePlanModel):
    kind: Literal["memstore_source"] = "memstore_source"
    parent: NonEmptyStrictStr
    child: NonEmptyStrictStr
    source_id: RuntimeMemstoreSourceId

    @model_validator(mode="after")
    def _different_products(self) -> "MemstoreRelationshipPlan":
        if self.parent == self.child:
            raise ValueError("relationship parent and child must differ")
        return self


RelationshipPlan = Annotated[
    NestedRelationshipPlan | MemstoreRelationshipPlan,
    Field(discriminator="kind"),
]


class UnresolvedCompileFact(CompilePlanModel):
    """A fact that cannot be proven statically and why."""

    product: NonEmptyStrictStr
    aspect: NonEmptyStrictStr
    reason: NonEmptyStrictStr


class ExactCountAcceptancePlan(CompilePlanModel):
    kind: Literal["exact_count"] = "exact_count"
    product: NonEmptyStrictStr
    exact_count: NonNegativeStrictInt


class PerParentCountAcceptancePlan(CompilePlanModel):
    kind: Literal["per_parent_count"] = "per_parent_count"
    product: NonEmptyStrictStr
    parent_product: NonEmptyStrictStr
    count_per_parent: PositiveStrictInt


class UniqueAcceptancePlan(CompilePlanModel):
    kind: Literal["unique"] = "unique"
    product: NonEmptyStrictStr
    field: NonEmptyStrictStr
    scope: Literal["global"] = "global"


class ForeignKeyAcceptancePlan(CompilePlanModel):
    kind: Literal["foreign_key"] = "foreign_key"
    product: NonEmptyStrictStr
    child_field: NonEmptyStrictStr
    parent_product: NonEmptyStrictStr
    parent_field: NonEmptyStrictStr


class AllowedValuesAcceptancePlan(CompilePlanModel):
    kind: Literal["allowed_values"] = "allowed_values"
    product: NonEmptyStrictStr
    field: NonEmptyStrictStr
    allowed_values: list[StrictStr] = Field(min_length=1)


class RangeAcceptancePlan(CompilePlanModel):
    kind: Literal["range"] = "range"
    product: NonEmptyStrictStr
    field: NonEmptyStrictStr
    minimum: StrictStr
    maximum: StrictStr

    @model_validator(mode="after")
    def _ordered_numeric_bounds(self) -> "RangeAcceptancePlan":
        try:
            minimum = Decimal(self.minimum)
            maximum = Decimal(self.maximum)
        except InvalidOperation as error:
            raise ValueError("range bounds must be decimal literals") from error
        if not minimum.is_finite() or not maximum.is_finite():
            raise ValueError("range bounds must be finite")
        if minimum > maximum:
            raise ValueError("minimum must not exceed maximum")
        return self


DerivedAcceptancePlan = Annotated[
    ExactCountAcceptancePlan
    | PerParentCountAcceptancePlan
    | UniqueAcceptancePlan
    | ForeignKeyAcceptancePlan
    | AllowedValuesAcceptancePlan
    | RangeAcceptancePlan,
    Field(discriminator="kind"),
]


class CompilePlan(CompilePlanModel):
    """Complete compiler-owned handoff for execution and acceptance stages."""

    products: list[ProductCompilePlan] = Field(min_length=1)
    relationships: list[RelationshipPlan] = Field(default_factory=list)
    unresolved: list[UnresolvedCompileFact] = Field(default_factory=list)
    derived_acceptance: list[DerivedAcceptancePlan] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_graph_integrity(self) -> "CompilePlan":
        products_by_name: dict[str, ProductCompilePlan] = {}
        fields_by_product: dict[str, dict[str, FieldPlan]] = {}
        for product in self.products:
            if product.name in products_by_name:
                raise ValueError(f"duplicate product name '{product.name}'")
            products_by_name[product.name] = product
            fields: dict[str, FieldPlan] = {}
            for field in product.fields:
                if field.name in fields:
                    raise ValueError(
                        f"duplicate field name '{field.name}' in product '{product.name}'"
                    )
                fields[field.name] = field
            fields_by_product[product.name] = fields

        def require_product(name: str, context: str) -> ProductCompilePlan:
            product = products_by_name.get(name)
            if product is None:
                raise ValueError(f"{context} references unknown product '{name}'")
            return product

        def require_field(product_name: str, field_name: str, context: str) -> FieldPlan:
            require_product(product_name, context)
            field = fields_by_product[product_name].get(field_name)
            if field is None:
                raise ValueError(
                    f"{context} references unknown field '{field_name}' "
                    f"on product '{product_name}'"
                )
            return field

        product_nested_edges: set[tuple[str, str]] = set()
        generated_products: dict[str, GeneratedProductCompilePlan] = {}
        for product in self.products:
            if not isinstance(product, GeneratedProductCompilePlan):
                continue
            generated_products[product.name] = product
            if product.parent is not None:
                parent = require_product(product.parent, f"generated product '{product.name}'")
                if not isinstance(parent, GeneratedProductCompilePlan):
                    raise ValueError(
                        f"generated parent '{product.parent}' must be a generated product"
                    )
                if product.name not in parent.children:
                    raise ValueError(
                        f"generated child '{product.name}' is not declared by parent "
                        f"'{parent.name}'"
                    )
            for child_name in product.children:
                child = require_product(child_name, f"generated product '{product.name}'")
                if not isinstance(child, GeneratedProductCompilePlan):
                    raise ValueError(f"generated child '{child_name}' must be a generated product")
                if child.parent != product.name:
                    raise ValueError(
                        f"generated child '{child_name}' does not reference parent "
                        f"'{product.name}'"
                    )
                product_nested_edges.add((product.name, child_name))

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit_generated(product_name: str) -> None:
            if product_name in visiting:
                raise ValueError(f"generated product graph contains a cycle at '{product_name}'")
            if product_name in visited:
                return
            visiting.add(product_name)
            product = generated_products[product_name]
            for child_name in product.children:
                visit_generated(child_name)
            visiting.remove(product_name)
            visited.add(product_name)

        for product_name in generated_products:
            visit_generated(product_name)

        for product in self.products:
            if (
                isinstance(product, SourceProductCompilePlan)
                and isinstance(product.source, MemstoreSourceBindingPlan)
                and product.source.product is not None
            ):
                require_product(
                    product.source.product,
                    f"memstore source product '{product.name}'",
                )

        nested_relationships: set[tuple[str, str]] = set()
        memstore_relationships: set[tuple[str, str]] = set()
        memstore_children: set[str] = set()
        for relationship in self.relationships:
            parent = require_product(relationship.parent, "relationship")
            child = require_product(relationship.child, "relationship")
            endpoints = (relationship.parent, relationship.child)
            if isinstance(relationship, NestedRelationshipPlan):
                if endpoints in nested_relationships:
                    raise ValueError(
                        f"duplicate nested relationship '{relationship.parent}' -> "
                        f"'{relationship.child}'"
                    )
                nested_relationships.add(endpoints)
                if endpoints not in product_nested_edges:
                    raise ValueError(
                        f"nested relationship '{relationship.parent}' -> "
                        f"'{relationship.child}' is inconsistent with product graph"
                    )
                if not isinstance(parent, GeneratedProductCompilePlan) or not isinstance(
                    child, GeneratedProductCompilePlan
                ):
                    raise ValueError("nested relationship endpoints must be generated products")
                continue

            if endpoints in memstore_relationships:
                raise ValueError(
                    f"duplicate memstore relationship '{relationship.parent}' -> "
                    f"'{relationship.child}'"
                )
            memstore_relationships.add(endpoints)
            if relationship.child in memstore_children:
                raise ValueError(
                    f"source product '{relationship.child}' has multiple memstore relationships"
                )
            memstore_children.add(relationship.child)
            if not isinstance(child, SourceProductCompilePlan) or not isinstance(
                child.source, MemstoreSourceBindingPlan
            ):
                raise ValueError("memstore relationship child must use a memstore source")
            if child.source.id != relationship.source_id:
                raise ValueError("memstore relationship source_id does not match child source")
            if child.source.product is not None and child.source.product != relationship.parent:
                raise ValueError("memstore relationship parent does not match child source product")
            if not any(
                isinstance(target, MemstoreTargetBindingPlan)
                and target.id == relationship.source_id
                for target in parent.targets
            ):
                raise ValueError("memstore relationship source_id does not match parent target")

        if nested_relationships != product_nested_edges:
            raise ValueError("nested product graph and relationship declarations differ")
        for product in self.products:
            if (
                isinstance(product, SourceProductCompilePlan)
                and isinstance(product.source, MemstoreSourceBindingPlan)
                and product.name not in memstore_children
            ):
                raise ValueError(
                    f"memstore source product '{product.name}' has no relationship declaration"
                )

        exact_facts: set[str] = set()
        per_parent_facts: set[tuple[str, str]] = set()
        unique_facts: set[tuple[str, str]] = set()
        foreign_key_facts: set[tuple[str, str, str, str]] = set()
        allowed_values_facts: set[tuple[str, str]] = set()
        range_facts: set[tuple[str, str]] = set()
        for acceptance in self.derived_acceptance:
            product = require_product(acceptance.product, "derived acceptance")
            if isinstance(acceptance, ExactCountAcceptancePlan):
                if acceptance.product in exact_facts:
                    raise ValueError(
                        f"duplicate exact-count acceptance for '{acceptance.product}'"
                    )
                exact_facts.add(acceptance.product)
                if acceptance.exact_count != product.static_count:
                    raise ValueError("exact-count acceptance does not match product static_count")
            elif isinstance(acceptance, PerParentCountAcceptancePlan):
                per_parent_fact = (acceptance.parent_product, acceptance.product)
                if per_parent_fact in per_parent_facts:
                    raise ValueError("duplicate per-parent acceptance")
                per_parent_facts.add(per_parent_fact)
                parent = require_product(
                    acceptance.parent_product,
                    "per-parent acceptance",
                )
                if not isinstance(parent, GeneratedProductCompilePlan) or not isinstance(
                    product, GeneratedProductCompilePlan
                ):
                    raise ValueError("per-parent acceptance requires generated products")
                if (
                    per_parent_fact not in product_nested_edges
                    or product.parent != parent.name
                ):
                    raise ValueError("per-parent acceptance does not match nested relationship")
                if acceptance.count_per_parent != product.count_per_parent:
                    raise ValueError("per-parent acceptance does not match child count_per_parent")
            elif isinstance(acceptance, UniqueAcceptancePlan):
                unique_fact = (acceptance.product, acceptance.field)
                if unique_fact in unique_facts:
                    raise ValueError("duplicate unique acceptance")
                unique_facts.add(unique_fact)
                field = require_field(
                    acceptance.product,
                    acceptance.field,
                    "unique acceptance",
                )
                has_identifier_role = any(
                    isinstance(role, IdentifierRolePlan) for role in field.roles
                )
                if field.kind is not FieldIntentKind.INTEGER_RANGE and not has_identifier_role:
                    raise ValueError(
                        "unique acceptance requires an integer range or identifier role"
                    )
            elif isinstance(acceptance, ForeignKeyAcceptancePlan):
                foreign_key_fact = (
                    acceptance.product,
                    acceptance.child_field,
                    acceptance.parent_product,
                    acceptance.parent_field,
                )
                if foreign_key_fact in foreign_key_facts:
                    raise ValueError("duplicate foreign-key acceptance")
                foreign_key_facts.add(foreign_key_fact)
                child_field = require_field(
                    acceptance.product,
                    acceptance.child_field,
                    "foreign-key acceptance",
                )
                require_field(
                    acceptance.parent_product,
                    acceptance.parent_field,
                    "foreign-key acceptance",
                )
                if not any(
                    isinstance(role, ForeignKeyRolePlan)
                    and role.parent_product == acceptance.parent_product
                    and role.parent_field == acceptance.parent_field
                    for role in child_field.roles
                ):
                    raise ValueError("foreign-key acceptance does not match child field role")
            elif isinstance(acceptance, AllowedValuesAcceptancePlan):
                allowed_values_fact = (acceptance.product, acceptance.field)
                if allowed_values_fact in allowed_values_facts:
                    raise ValueError("duplicate allowed-values acceptance")
                allowed_values_facts.add(allowed_values_fact)
                field = require_field(
                    acceptance.product,
                    acceptance.field,
                    "allowed-values acceptance",
                )
                if field.kind not in (FieldIntentKind.VALUES, FieldIntentKind.WEIGHTED):
                    raise ValueError(
                        "allowed-values acceptance requires values or weighted field intent"
                    )
            elif isinstance(acceptance, RangeAcceptancePlan):
                range_fact = (acceptance.product, acceptance.field)
                if range_fact in range_facts:
                    raise ValueError("duplicate range acceptance")
                range_facts.add(range_fact)
                field = require_field(
                    acceptance.product,
                    acceptance.field,
                    "range acceptance",
                )
                if field.kind not in (
                    FieldIntentKind.INTEGER_RANGE,
                    FieldIntentKind.DECIMAL_RANGE,
                ):
                    raise ValueError("range acceptance requires a numeric range field intent")

        unresolved_facts: set[tuple[str, str]] = set()
        for unresolved in self.unresolved:
            require_product(unresolved.product, "unresolved fact")
            unresolved_fact = (unresolved.product, unresolved.aspect)
            if unresolved_fact in unresolved_facts:
                raise ValueError(
                    f"duplicate unresolved fact '{unresolved.aspect}' for "
                    f"'{unresolved.product}'"
                )
            unresolved_facts.add(unresolved_fact)
        return self


class AcceptanceStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    UNEVALUABLE = "unevaluable"


class AcceptanceSource(StrEnum):
    DERIVED = "derived"
    EXPLICIT = "explicit"
    DERIVED_AND_EXPLICIT = "derived_and_explicit"


class CaptureCompletenessStatus(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


class ProductCaptureCompleteness(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    product: str
    status: CaptureCompletenessStatus
    reason: str
    runtime_status: CaptureStatus | None = None
    requested: NonNegativeStrictInt | None = None
    observed: NonNegativeStrictInt | None = None
    limit: PositiveStrictInt | None = None


class CaptureCompletenessEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: CaptureCompletenessStatus
    products: list[ProductCaptureCompleteness]


class AcceptanceResultBase(BaseModel):
    """Shared, transport-neutral evidence for one mandatory expectation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: AcceptanceStatus
    source: AcceptanceSource
    mandatory: Literal[True] = True
    message: str
    capture_completeness: CaptureCompletenessEvidence | None = None

    def with_capture_completeness(
        self,
        evidence: CaptureCompletenessEvidence,
    ) -> Self:
        return self.model_copy(update={"capture_completeness": evidence})


class ExactCountAcceptanceResult(AcceptanceResultBase):
    kind: Literal["exact_count"] = "exact_count"
    product: str
    expected_count: int
    observed_count: int | None


class PerParentCountAcceptanceResult(AcceptanceResultBase):
    kind: Literal["per_parent_count"] = "per_parent_count"
    product: str
    parent_product: str
    expected_count_per_parent: int
    parent_field: str | None = None
    child_field: str | None = None
    observed_counts: dict[str, int] | None = None


class UniqueAcceptanceResult(AcceptanceResultBase):
    kind: Literal["unique"] = "unique"
    product: str
    field: str
    scope: Literal["global", "per_parent"]
    observed_count: int | None
    distinct_count: int | None
    duplicate_values: list[str] = Field(default_factory=list)


class ForeignKeyAcceptanceResult(AcceptanceResultBase):
    kind: Literal["foreign_key"] = "foreign_key"
    product: str
    child_field: str
    parent_product: str
    parent_field: str
    observed_count: int | None
    missing_values: list[str] = Field(default_factory=list)


class AllowedValuesAcceptanceResult(AcceptanceResultBase):
    kind: Literal["allowed_values"] = "allowed_values"
    product: str
    field: str
    allowed_values: list[str]
    observed_count: int | None
    unexpected_values: list[str] = Field(default_factory=list)


class RangeAcceptanceResult(AcceptanceResultBase):
    kind: Literal["range"] = "range"
    product: str
    field: str
    expected_minimum: str
    expected_maximum: str
    observed_minimum: str | None = None
    observed_maximum: str | None = None
    violating_rows: list[int] = Field(default_factory=list)


class RowConditionAcceptanceResult(AcceptanceResultBase):
    kind: Literal["row_condition"] = "row_condition"
    product: str
    condition: str
    observed_count: int | None
    failed_rows: list[int] = Field(default_factory=list)
    evaluation_errors: list[str] = Field(default_factory=list)


class MemstoreCompletenessAcceptanceResult(AcceptanceResultBase):
    kind: Literal["memstore_completeness"] = "memstore_completeness"
    producer_product: str
    consumer_product: str
    source_id: str
    producer_count: int | None
    consumer_count: int | None
    producer_key_field: str | None = None
    consumer_key_field: str | None = None
    missing_keys: list[str] = Field(default_factory=list)
    unexpected_keys: list[str] = Field(default_factory=list)
    duplicate_producer_keys: list[str] = Field(default_factory=list)
    duplicate_consumer_keys: list[str] = Field(default_factory=list)


AcceptanceResult = Annotated[
    ExactCountAcceptanceResult
    | PerParentCountAcceptanceResult
    | UniqueAcceptanceResult
    | ForeignKeyAcceptanceResult
    | AllowedValuesAcceptanceResult
    | RangeAcceptanceResult
    | RowConditionAcceptanceResult
    | MemstoreCompletenessAcceptanceResult,
    Field(discriminator="kind"),
]


class AcceptanceReport(BaseModel):
    """Canonical acceptance response derived from one captured bounded run."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    verified: bool
    passed: int
    failed: int
    unevaluable: int
    results: list[AcceptanceResult] = Field(default_factory=list)


class RunResult(BaseModel):
    """Canonical response contract for safe descriptor dry-runs."""

    ok: bool
    stage: AuthoringStage
    timing_ms: int | None = None
    products: list[ProductResult] = Field(default_factory=list)
    products_truncated: int = 0
    lint: CheckResult | None = None
    diagnostics: list[Diagnostic] = Field(default_factory=list)


class ScaffoldResult(BaseModel):
    """Canonical response contract for scaffold operations."""

    ok: bool = Field(description="Whether the operation succeeded")
    stage: AuthoringStage = Field(description="Canonical lifecycle stage reached")
    xml: str | None = Field(
        None,
        description="Rendered DATAMIMIC descriptor XML (None only on render error)",
    )
    error: str | None = Field(
        None,
        description="Compatibility summary projected from issues when stage=render",
    )
    issues: list[IntentValidationIssue] = Field(
        default_factory=list,
        description="Canonical repair-oriented intent validation issues",
    )
    summary: str | None = Field(
        None,
        description="Lint summary if stage=lint",
    )
    diagnostics: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Lint or dry-run diagnostics (verbosity controlled by response_format)",
    )
    truncated: bool = Field(
        False,
        description="Diagnostics truncated due to max_diagnostics limit",
    )
    products: list[ProductResult] = Field(
        default_factory=list,
        description="Captured sample rows per product (when execution completed)",
    )
    normalization_notes: list[str] = Field(
        default_factory=list,
        description="Notes from schema normalization (e.g. kind aliases applied)",
    )
    compile_plan: CompilePlan | None = None
    acceptance: AcceptanceReport | None = None
    verification: ScaffoldVerificationEvidence = Field(
        default_factory=ScaffoldVerificationEvidence
    )
    verified: bool = False

    @model_validator(mode="after")
    def _verified_requires_all_evidence(self) -> Self:
        if self.verified and (
            self.acceptance is None
            or not self.acceptance.verified
            or not self.verification.gates_passed
        ):
            raise ValueError(
                "verified requires passing acceptance and every requested verification gate"
            )
        return self
