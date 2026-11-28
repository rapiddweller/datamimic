# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""What a ready Build did not check: typed coverage facts and the warnings that they raise."""

from __future__ import annotations

from collections.abc import Iterable
from enum import StrEnum
from pathlib import PurePosixPath
from typing import Annotated

from pydantic import Field, JsonValue, StrictBool, model_validator

from datamimic_ce.engine.dsl.vocabulary.constants.exporter_constants import EXPORTER_OUTPUT_DIR

from .build_rules import catalog_diagnostic
from .common import AuthoringModel, NonEmptyStrictStr, NonNegativeStrictInt, WorkspaceDescriptorPath
from .diagnostics import AuthoringRuleId, Diagnostic, DiagnosticPhase
from .expectations import DeclaredSinkIdentity, ExpectationIntentKind, ExpectationSubject
from .proof import AcceptanceOrigin

# A file with one of these suffixes holds project data. Other files (scripts, notes, XML steps) are not data.
DATA_FILE_SUFFIXES = frozenset((".csv", ".json", ".jsonl", ".txt", ".xlsx", ".parquet"))
# The acceptance and the environment profile are read by Build itself, not by the model. The exporter output is
# what a run wrote, not an input.
NON_DATA_ROOTS = frozenset(("acceptance", "conf", EXPORTER_OUTPUT_DIR))
# Documentation and libraries are not model inputs, at any depth.
NON_DATA_FOLDERS = frozenset(("docs", "lib"))
NON_DATA_NAME_PREFIXES = ("readme", "license", "notes", "changelog")


class CoverageGapKind(StrEnum):
    """The name of each open gap; the value is the `BuildCoverage` field that holds its facts."""

    PRODUCTS_WITHOUT_EXPECTATION = "products_without_expectation"
    UNREAD_DATA_FILES = "unread_data_files"
    UNCHECKED_DECLARED_SINKS = "unchecked_declared_sinks"
    SEEDED = "seeded"


class ProductCoverage(AuthoringModel):
    product: NonEmptyStrictStr
    expectations: NonNegativeStrictInt = Field(description="Number of expectations that name this product.")


class BuildCoverage(AuthoringModel):
    """Counted facts about what the acceptance and the bounded run covered; each gap raises a warning."""

    expectation_count: NonNegativeStrictInt
    products: tuple[ProductCoverage, ...]
    products_without_expectation: tuple[NonEmptyStrictStr, ...] = Field(
        description="Products that no expectation names. Their values are not checked."
    )
    unread_data_files: tuple[WorkspaceDescriptorPath, ...] = Field(
        description="Project data files that the bounded run never opened. The model does not use them."
    )
    unchecked_declared_sinks: tuple[DeclaredSinkIdentity, ...] = Field(
        description="Declared sinks that no expectation on a declared sink covers."
    )
    seeded: StrictBool = Field(description="False when the project sets no rngSeed. Then no replay ran.")

    @property
    def has_gaps(self) -> bool:
        return bool(self.open_gaps)

    @property
    def open_gaps(self) -> tuple[CoverageGapKind, ...]:
        return tuple(kind for kind, _ in self._gaps())

    def action_required(self) -> str | None:
        """The one line that stops an agent from reporting success on a Ready with open gaps."""
        gaps = self.open_gaps
        if not gaps:
            return None
        noun = "gap" if len(gaps) == 1 else "gaps"
        names = ", ".join(kind.value for kind in gaps)
        return (
            f"Ready with {len(gaps)} open coverage {noun} ({names}). "
            "Do not report success until each gap is fixed or explained."
        )

    def warnings(self) -> tuple[Diagnostic, ...]:
        """One warning for each gap, with counted facts in `actual`."""
        return tuple(warning for _, warning in self._gaps())

    def _gaps(self) -> tuple[tuple[CoverageGapKind, Diagnostic], ...]:
        """The one place that decides which gaps are open: each open gap with its warning, in declared order."""
        found: list[tuple[CoverageGapKind, Diagnostic]] = []

        def gap(kind: CoverageGapKind, message: str, actual: tuple[str, ...] | None, remediation: str) -> None:
            listed: JsonValue = None if actual is None else list(actual)
            warning = catalog_diagnostic(
                AuthoringRuleId.COVERAGE_GAP,
                message,
                phase=DiagnosticPhase.EVIDENCE,
                path=("coverage", kind.value),
                actual=listed,
                remediation=remediation,
            )
            found.append((kind, warning))

        if self.products_without_expectation:
            gap(
                CoverageGapKind.PRODUCTS_WITHOUT_EXPECTATION,
                "Some products have no expectation, so their values are not checked.",
                self.products_without_expectation,
                "Add an expectation for each listed product in acceptance/build.json.",
            )
        if self.unread_data_files:
            gap(
                CoverageGapKind.UNREAD_DATA_FILES,
                "Some project data files were never read by the run, so the model does not use them.",
                tuple(str(path) for path in self.unread_data_files),
                "Read each listed file with a source in the model, move it to docs/, or delete it.",
            )
        if self.unchecked_declared_sinks:
            gap(
                CoverageGapKind.UNCHECKED_DECLARED_SINKS,
                "Some declared sinks have no expectation on the sink.",
                tuple(f"{sink.kind}:{sink.environment}:{sink.entity}" for sink in self.unchecked_declared_sinks),
                "Add an expectation whose subject is the declared sink.",
            )
        if not self.seeded:
            gap(
                CoverageGapKind.SEEDED,
                "The project sets no rngSeed, so Build ran it once and did not replay it.",
                None,
                "Set rngSeed on the setup element.",
            )
        return tuple(found)


def _is_project_data(path: PurePosixPath) -> bool:
    name: str = path.name
    lowered: str = name.lower()
    suffix: str = path.suffix
    return (
        suffix.lower() in DATA_FILE_SUFFIXES
        and path.parts[0] not in NON_DATA_ROOTS
        and not any(folder in NON_DATA_FOLDERS for folder in path.parts[:-1])
        and not lowered.startswith(NON_DATA_NAME_PREFIXES)
    )


def unread_data_files(
    workspace_files: Iterable[PurePosixPath],
    read_paths: Iterable[PurePosixPath],
    parent_read: Iterable[PurePosixPath],
) -> tuple[PurePosixPath, ...]:
    """Data files of the workspace that neither Build nor the audit hook saw opened.

    EE adds a `source_accesses` argument for native readers (parquet) that open files outside the audit hook. CE has
    no such reader, so a project `.parquet` file is always reported; a later reader adds the argument here.
    """
    used = {*read_paths, *parent_read}
    return tuple(sorted(path for path in workspace_files if _is_project_data(path) and path not in used))


# The MCP server refuses a result over 60 000 characters; one item of this list needs 150 to 210 of them.
MAX_LISTED_EXPECTATIONS = 100


class ExpectationResult(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    # The run stopped, or its capture was incomplete, before Build could evaluate the expectation.
    NOT_EVALUATED = "not_evaluated"


class ListedExpectation(AuthoringModel):
    origin: AcceptanceOrigin = Field(
        description="model: in expectations. caller: in acceptance_requirements. derived: Build added it."
    )
    kind: ExpectationIntentKind
    subject: Annotated[ExpectationSubject, Field(discriminator="kind")] = Field(
        description="The row set that the expectation checks; for a foreign_key, the referencing (child) side."
    )
    field: NonEmptyStrictStr | None = Field(
        description="The checked field; none for a count or a row condition. For a foreign_key, the child field."
    )
    result: ExpectationResult


class ListedExpectations(AuthoringModel):
    """Counted facts, not rows: at most `MAX_LISTED_EXPECTATIONS` items, in the order that Build checks them."""

    total: NonNegativeStrictInt = Field(description="Every expectation of the acceptance, listed or not.")
    truncated: StrictBool = Field(description="True when total is above the number of items.")
    items: tuple[ListedExpectation, ...]

    @model_validator(mode="after")
    def items_are_the_first_of_total_up_to_the_cap(self) -> ListedExpectations:
        if len(self.items) != min(self.total, MAX_LISTED_EXPECTATIONS) or self.truncated != (
            self.total > MAX_LISTED_EXPECTATIONS
        ):
            raise ValueError(
                "the items must be the first MAX_LISTED_EXPECTATIONS of the total, and truncated must say so"
            )
        return self


__all__ = [
    "MAX_LISTED_EXPECTATIONS",
    "BuildCoverage",
    "CoverageGapKind",
    "ExpectationResult",
    "ListedExpectation",
    "ListedExpectations",
    "ProductCoverage",
    "unread_data_files",
]
