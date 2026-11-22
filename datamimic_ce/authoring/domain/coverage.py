# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""What a ready Build did not check: typed coverage facts and the warnings that they raise."""

from __future__ import annotations

from collections.abc import Iterable
from enum import StrEnum
from pathlib import PurePosixPath

from pydantic import Field, JsonValue, StrictBool

from datamimic_ce.engine.dsl.vocabulary.constants.exporter_constants import EXPORTER_OUTPUT_DIR

from .build_rules import catalog_diagnostic
from .common import AuthoringModel, NonEmptyStrictStr, NonNegativeStrictInt, WorkspaceDescriptorPath
from .diagnostics import AuthoringRuleId, Diagnostic, DiagnosticPhase
from .expectations import DeclaredSinkIdentity

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
        return bool(
            self.products_without_expectation
            or self.unread_data_files
            or self.unchecked_declared_sinks
            or not self.seeded
        )

    @property
    def open_gaps(self) -> tuple[CoverageGapKind, ...]:
        flags = (
            (CoverageGapKind.PRODUCTS_WITHOUT_EXPECTATION, bool(self.products_without_expectation)),
            (CoverageGapKind.UNREAD_DATA_FILES, bool(self.unread_data_files)),
            (CoverageGapKind.UNCHECKED_DECLARED_SINKS, bool(self.unchecked_declared_sinks)),
            (CoverageGapKind.SEEDED, not self.seeded),
        )
        return tuple(kind for kind, open_ in flags if open_)

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
        found: list[Diagnostic] = []
        if self.products_without_expectation:
            found.append(
                _warning(
                    "Some products have no expectation, so their values are not checked.",
                    ("coverage", "products_without_expectation"),
                    self.products_without_expectation,
                    "Add an expectation for each listed product in acceptance/build.json.",
                )
            )
        if self.unread_data_files:
            found.append(
                _warning(
                    "Some project data files were never read by the run, so the model does not use them.",
                    ("coverage", "unread_data_files"),
                    tuple(str(path) for path in self.unread_data_files),
                    "Read each listed file with a source in the model, move it to docs/, or delete it.",
                )
            )
        if self.unchecked_declared_sinks:
            found.append(
                _warning(
                    "Some declared sinks have no expectation on the sink.",
                    ("coverage", "unchecked_declared_sinks"),
                    tuple(f"{sink.kind}:{sink.environment}:{sink.entity}" for sink in self.unchecked_declared_sinks),
                    "Add an expectation whose subject is the declared sink.",
                )
            )
        if not self.seeded:
            found.append(
                _warning(
                    "The project sets no rngSeed, so Build ran it once and did not replay it.",
                    ("coverage", "seeded"),
                    None,
                    "Set rngSeed on the setup element.",
                )
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


def _warning(message: str, path: tuple[str, ...], actual: tuple[str, ...] | None, remediation: str) -> Diagnostic:
    listed: JsonValue = None if actual is None else list(actual)
    return catalog_diagnostic(
        AuthoringRuleId.COVERAGE_GAP,
        message,
        phase=DiagnosticPhase.EVIDENCE,
        path=path,
        actual=listed,
        remediation=remediation,
    )


__all__ = ["BuildCoverage", "CoverageGapKind", "ProductCoverage", "unread_data_files"]
