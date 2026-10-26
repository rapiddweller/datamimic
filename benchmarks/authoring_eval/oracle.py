# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Blind-agent eval oracle (#412): judge a project by the rows it produces, never by its own acceptance file.

    python -m benchmarks.authoring_eval.oracle <case-id> <project-dir>

Builds the project, runs it, captures the rows per product and evaluates ``cases/<id>/oracle.json``. The verdict
is JSON with one reason per check and never contains a row value."""

import argparse
import contextlib
import json
import shutil
import sys
import tempfile
from abc import ABC, abstractmethod
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.domain.requests import PROJECT_ENTRY_PATH, ReadyBuild
from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest

CASES = Path(__file__).resolve().parent / "cases"

Row = dict[str, object]
Scalar = StrictStr | StrictInt


@dataclass(frozen=True)
class Observed:
    """What the project did when built and run in a private copy."""

    build_note: str | None  # None when Build reached ready, else a short outcome description
    run_error: str | None  # exception class name when the run failed
    rows: dict[str, list[Row]] = field(default_factory=dict)
    json_outputs: dict[str, list[object]] = field(default_factory=dict)  # file stem -> parsed JSON array


def _product_rows(observed: Observed, product: str) -> list[Row] | str:
    """The product's rows, or the reason there are none."""
    if observed.run_error is not None:
        return f"run failed: {observed.run_error}"
    if product not in observed.rows:
        return f"product {product} was not produced"
    return observed.rows[product]


class _Check(BaseModel, ABC):
    model_config = ConfigDict(extra="forbid", frozen=True)

    @abstractmethod
    def label(self) -> str: ...

    @abstractmethod
    def failure(self, observed: Observed) -> str | None:
        """None when the check holds, else a short reason without row values."""

    def _rows(self, observed: Observed, product: str) -> list[Row] | str:
        return _product_rows(observed, product)


class BuildReady(_Check):
    kind: Literal["build_ready"]

    def label(self) -> str:
        return "build_ready"

    def failure(self, observed: Observed) -> str | None:
        return observed.build_note


class ExactCount(_Check):
    kind: Literal["exact_count"]
    product: str
    n: int

    def label(self) -> str:
        return f"exact_count:{self.product}"

    def failure(self, observed: Observed) -> str | None:
        rows = self._rows(observed, self.product)
        if isinstance(rows, str):
            return rows
        return None if len(rows) == self.n else f"{len(rows)} rows, expected {self.n}"


class Unique(_Check):
    kind: Literal["unique"]
    product: str
    field: str

    def label(self) -> str:
        return f"unique:{self.product}.{self.field}"

    def failure(self, observed: Observed) -> str | None:
        rows = self._rows(observed, self.product)
        if isinstance(rows, str):
            return rows
        values = [row.get(self.field) for row in rows]
        if not all(isinstance(value, str | int | float) for value in values):
            return "values are missing or not scalar"
        return None if len(set(values)) == len(values) else f"{len(values) - len(set(values))} duplicate values"


class FieldRef(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    product: str
    field: str

    def values(self, observed: Observed) -> list[object] | str:
        """The field's value in every row, or the reason they cannot be read."""
        rows = _product_rows(observed, self.product)
        if isinstance(rows, str):
            return rows
        if any(self.field not in row for row in rows):
            return f"{self.product}.{self.field} is missing from some rows"
        return [row[self.field] for row in rows]

    def __str__(self) -> str:
        return f"{self.product}.{self.field}"


class PerParentCount(_Check):
    kind: Literal["per_parent_count"]
    child: FieldRef  # the child field that holds the parent key
    parent: FieldRef
    n: int

    def label(self) -> str:
        return f"per_parent_count:{self.child}"

    def failure(self, observed: Observed) -> str | None:
        children, parents = self.child.values(observed), self.parent.values(observed)
        if isinstance(children, str):
            return children
        if isinstance(parents, str):
            return parents
        owned = Counter(str(value) for value in children)
        wrong = [key for key in parents if owned[str(key)] != self.n]
        return None if not wrong else f"{len(wrong)} of {len(parents)} parents do not own exactly {self.n} children"


class FkInParent(_Check):
    kind: Literal["fk_in_parent"]
    child: FieldRef
    parent: FieldRef

    def label(self) -> str:
        return f"fk_in_parent:{self.child}"

    def failure(self, observed: Observed) -> str | None:
        children, parents = self.child.values(observed), self.parent.values(observed)
        if isinstance(children, str):
            return children
        if isinstance(parents, str):
            return parents
        keys = {str(value) for value in parents}
        orphans = [value for value in children if str(value) not in keys]
        return None if not orphans else f"{len(orphans)} child rows reference no parent"


class ValueIn(_Check):
    kind: Literal["value_in"]
    product: str
    field: str
    values: list[Scalar]

    def label(self) -> str:
        return f"value_in:{self.product}.{self.field}"

    def failure(self, observed: Observed) -> str | None:
        found = FieldRef(product=self.product, field=self.field).values(observed)
        if isinstance(found, str):
            return found
        outside = [value for value in found if value not in self.values]
        return None if not outside else f"{len(outside)} values outside the allowed set"


class InRange(_Check):
    kind: Literal["range"]
    product: str
    field: str
    min: int
    max: int

    def label(self) -> str:
        return f"range:{self.product}.{self.field}"

    def failure(self, observed: Observed) -> str | None:
        found = FieldRef(product=self.product, field=self.field).values(observed)
        if isinstance(found, str):
            return found
        # bool is an int subclass but never a whole number in a data row
        bad = [v for v in found if isinstance(v, bool) or not isinstance(v, int) or not self.min <= v <= self.max]
        return None if not bad else f"{len(bad)} values are not whole numbers in {self.min}..{self.max}"


class FieldPresent(_Check):
    kind: Literal["field_present"]
    product: str
    fields: list[str]

    def label(self) -> str:
        return f"field_present:{self.product}"

    def failure(self, observed: Observed) -> str | None:
        rows = self._rows(observed, self.product)
        if isinstance(rows, str):
            return rows
        empty = [name for name in self.fields if any(row.get(name) in (None, "") for row in rows)]
        return None if not empty else f"missing or empty in some rows: {', '.join(empty)}"


class ExactFields(_Check):
    kind: Literal["exact_fields"]
    product: str
    fields: list[str]

    def label(self) -> str:
        return f"exact_fields:{self.product}"

    def failure(self, observed: Observed) -> str | None:
        rows = self._rows(observed, self.product)
        if isinstance(rows, str):
            return rows
        odd = sum(1 for row in rows if set(row) != set(self.fields))
        return None if not odd else f"{odd} rows do not have exactly the expected fields"


class FieldAtMost(_Check):
    kind: Literal["field_at_most"]
    product: str
    field: str
    other: str

    def label(self) -> str:
        return f"field_at_most:{self.product}.{self.field}"

    def failure(self, observed: Observed) -> str | None:
        rows = self._rows(observed, self.product)
        if isinstance(rows, str):
            return rows
        bad = 0
        for row in rows:
            left, right = row.get(self.field), row.get(self.other)
            if not (isinstance(left, int | float) and isinstance(right, int | float) and left <= right):
                bad += 1
        return None if not bad else f"{bad} rows where {self.field} is not a number at most {self.other}"


class ExactRows(_Check):
    kind: Literal["exact_rows"]
    product: str
    rows: list[dict[str, Scalar]]

    def label(self) -> str:
        return f"exact_rows:{self.product}"

    def failure(self, observed: Observed) -> str | None:
        found = self._rows(observed, self.product)
        if isinstance(found, str):
            return found
        wanted = Counter(json.dumps(row, sort_keys=True) for row in self.rows)
        # default=str: a subject row can hold any type, and that must be a failed check, not a crash
        produced = Counter(json.dumps(row, sort_keys=True, default=str) for row in found)
        return None if wanted == produced else "produced rows differ from the expected rows"


class OutputRows(_Check):
    """The project wrote ``<product>.json`` (the JSON exporter) holding n rows."""

    kind: Literal["output_rows"]
    product: str
    n: int

    def label(self) -> str:
        return f"output_rows:{self.product}"

    def failure(self, observed: Observed) -> str | None:
        if observed.run_error is not None:
            return f"run failed: {observed.run_error}"
        written = observed.json_outputs.get(self.product)
        if written is None:
            return f"no {self.product}.json was written"
        return None if len(written) == self.n else f"{len(written)} rows written, expected {self.n}"


Check = Annotated[
    BuildReady
    | ExactCount
    | Unique
    | PerParentCount
    | FkInParent
    | ValueIn
    | InRange
    | FieldPresent
    | ExactFields
    | FieldAtMost
    | ExactRows
    | OutputRows,
    Field(discriminator="kind"),
]


class OracleSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    checks: list[Check]


class CheckResult(BaseModel):
    check: str
    passed: bool
    reason: str


class Verdict(BaseModel):
    case: str
    passed: bool
    checks: list[CheckResult]


def json_outputs(work: Path) -> dict[str, list[object]]:
    """Every JSON array the run wrote under output/, by file stem; a file that is not one JSON array is skipped."""
    found: dict[str, list[object]] = {}
    for path in work.glob("output/**/*.json"):
        try:
            parsed = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:  # includes JSONDecodeError; an NDJSON or truncated file is not "written" for the oracle
            continue
        if isinstance(parsed, list):
            found[path.stem] = parsed
    return found


def _observe(case: str, project: Path) -> Observed:
    """Build and run a private copy, with the case's fixtures laid over it so the agent cannot change them."""
    with tempfile.TemporaryDirectory() as scratch:
        work = Path(scratch) / "project"
        # output/ holds files from the agent's own runs; only this oracle run may write there
        shutil.copytree(project, work, ignore=shutil.ignore_patterns("output"))
        fixtures = CASES / case / "fixtures"
        if fixtures.is_dir():
            shutil.copytree(fixtures, work / fixtures.name, dirs_exist_ok=True)
        build = create_authoring_application(work, descriptor_path=PROJECT_ENTRY_PATH).build()
        build_note = None if isinstance(build, ReadyBuild) else f"Build {build.outcome} in phase {build.phase.value}"
        try:
            engine = DataMimicTest(test_dir=work, filename=PROJECT_ENTRY_PATH, capture_test_result=True)
            engine.test_with_timer()
        except Exception as error:  # an untrusted project can fail in any way; the class name is the whole reason
            return Observed(build_note, type(error).__name__)
        captured = engine.capture_result() or {}
        rows = {product: [dict(row) for row in product_rows] for product, product_rows in captured.items()}
        return Observed(build_note, None, rows, json_outputs(work))


def evaluate(case: str, project: Path) -> Verdict:
    spec = OracleSpec.model_validate_json((CASES / case / "oracle.json").read_text(encoding="utf-8"))
    observed = _observe(case, project)
    results = []
    for check in spec.checks:
        reason = check.failure(observed)
        results.append(CheckResult(check=check.label(), passed=reason is None, reason=reason or "ok"))
    return Verdict(case=case, passed=all(result.passed for result in results), checks=results)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="python -m benchmarks.authoring_eval.oracle")
    parser.add_argument("case", choices=sorted(path.name for path in CASES.iterdir() if path.is_dir()))
    parser.add_argument("project", type=Path)
    arguments = parser.parse_args(argv)
    with contextlib.redirect_stdout(sys.stderr):  # the engine logs to stdout; keep stdout one JSON document
        verdict = evaluate(arguments.case, arguments.project)
    print(verdict.model_dump_json(indent=2))
    return 0 if verdict.passed else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
