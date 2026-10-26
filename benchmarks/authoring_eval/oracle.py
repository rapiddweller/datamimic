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
import os
import shutil
import subprocess
import sys
import tempfile
from abc import ABC, abstractmethod
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated, Literal

from lxml import etree
from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr

from benchmarks.authoring_eval.capture import Capture
from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.domain.requests import PROJECT_ENTRY_PATH, ReadyBuild
from datamimic_ce.engine.dsl.api import DTDForbiddenError, parse_xml_file

CASES = Path(__file__).resolve().parent / "cases"
REPO_ROOT = Path(__file__).resolve().parents[2]
_RUN_TIMEOUT_SECONDS = 120
# Fixed and different for the two runs: the verdict stays reproducible, and a value that depends on the hash order
# of strings (which the interpreter randomises per process) differs between the runs.
_HASH_SEEDS = ("1", "2")
# The case directory that the main runs lay over the project, at the same path in the copy.
_FIXTURES = "fixtures"
_ENV_KEYS = ("HOME", "USER", "LOGNAME", "LANG", "TMPDIR", "SHELL")
_SYSTEM_PATH = "/usr/bin:/bin:/usr/sbin:/sbin"

Row = dict[str, object]
Scalar = StrictStr | StrictInt


@dataclass(frozen=True)
class Output:
    """The JSON files of one run."""

    error: str | None  # exception class name when the run failed
    files: dict[str, list[object]] = field(default_factory=dict)  # file stem -> parsed JSON array


@dataclass(frozen=True)
class Observed:
    """What the project did when built and run in a private copy."""

    build_note: str | None  # None when Build reached ready, else a short outcome description
    run_error: str | None  # exception class name when the run failed
    rows: dict[str, list[Row]] = field(default_factory=dict)
    outputs: dict[str, Output] = field(default_factory=dict)  # fixtures directory name -> the run with it
    declared_seed: str | None = None  # rngSeed of the entry descriptor's <setup>, None when absent
    second_rows: dict[str, list[Row]] | None = None  # rows of a second run in a fresh interpreter
    second_error: str | None = None


def _product_rows(observed: Observed, product: str) -> list[Row] | str:
    """The product's rows, or the reason there are none."""
    if observed.run_error is not None:
        return f"run failed: {observed.run_error}"
    if product not in observed.rows:
        return f"product {product} was not produced"
    return observed.rows[product]


def _row_difference(found: list[Row] | list[object], wanted: list[dict[str, Scalar]]) -> str | None:
    """None when both hold the same rows in any order, with the same keys and JSON types."""
    expected = Counter(json.dumps(row, sort_keys=True) for row in wanted)
    # default=str: a subject row can hold any type, and that must be a failed check, not a crash
    produced = Counter(json.dumps(row, sort_keys=True, default=str) for row in found)
    return None if expected == produced else "produced rows differ from the expected rows"


class _Check(BaseModel, ABC):
    model_config = ConfigDict(extra="forbid", frozen=True)

    @abstractmethod
    def label(self) -> str: ...

    @abstractmethod
    def failure(self, observed: Observed) -> str | None:
        """None when the check holds, else a short reason without row values."""


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
        rows = _product_rows(observed, self.product)
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
        rows = _product_rows(observed, self.product)
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
        rows = _product_rows(observed, self.product)
        if isinstance(rows, str):
            return rows
        empty = [name for name in self.fields if any(row.get(name) in (None, "") for row in rows)]
        return None if not empty else f"missing or empty in some rows: {', '.join(empty)}"


class FieldAtMost(_Check):
    kind: Literal["field_at_most"]
    product: str
    field: str
    other: str

    def label(self) -> str:
        return f"field_at_most:{self.product}.{self.field}"

    def failure(self, observed: Observed) -> str | None:
        rows = _product_rows(observed, self.product)
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
        found = _product_rows(observed, self.product)
        if isinstance(found, str):
            return found
        return _row_difference(found, self.rows)


class OutputRows(_Check):
    """A run with the case directory ``fixtures`` laid over ``fixtures/`` wrote ``<product>.json`` (the JSON
    exporter) holding exactly ``rows``. A changed fixtures directory proves that the rows come from the input."""

    kind: Literal["output_rows"]
    product: str
    fixtures: str = _FIXTURES
    rows: list[dict[str, Scalar]]

    def label(self) -> str:
        return f"output_rows:{self.product}:{self.fixtures}"

    def failure(self, observed: Observed) -> str | None:
        output = observed.outputs.get(self.fixtures)
        if output is None:
            return f"no run with {self.fixtures}"
        if output.error is not None:
            return f"run failed: {output.error}"
        written = output.files.get(self.product)
        if written is None:
            return f"no {self.product}.json was written"
        return _row_difference(written, self.rows)


class WholeNumber(_Check):
    """Every value is a Python int; a bool, float or text is not a whole number."""

    kind: Literal["whole_number"]
    product: str
    field: str

    def label(self) -> str:
        return f"whole_number:{self.product}.{self.field}"

    def failure(self, observed: Observed) -> str | None:
        found = FieldRef(product=self.product, field=self.field).values(observed)
        if isinstance(found, str):
            return found
        bad = [value for value in found if isinstance(value, bool) or not isinstance(value, int)]
        return None if not bad else f"{len(bad)} values are not whole numbers"


class SeedIs(_Check):
    """The entry descriptor's <setup rngSeed> is the seed that the case prescribes."""

    kind: Literal["seed_is"]
    seed: int

    def label(self) -> str:
        return "seed_is"

    def failure(self, observed: Observed) -> str | None:
        if observed.declared_seed is None:
            return "the entry descriptor declares no rngSeed"
        # an XML attribute is text, so compare with the text of the prescribed number
        return None if observed.declared_seed == str(self.seed) else "rngSeed is not the prescribed seed"


class Repeatable(_Check):
    """A second run, in a fresh interpreter, produces the same rows in the same order."""

    kind: Literal["repeatable"]

    def label(self) -> str:
        return "repeatable"

    def failure(self, observed: Observed) -> str | None:
        if observed.run_error is not None:
            return f"run failed: {observed.run_error}"
        if observed.second_error is not None:
            return f"second run failed: {observed.second_error}"
        second = observed.second_rows or {}
        differing = sorted(
            name for name in observed.rows.keys() | second.keys() if observed.rows.get(name) != second.get(name)
        )
        return None if not differing else f"two runs produced different rows in: {', '.join(differing)}"


Check = Annotated[
    BuildReady
    | ExactCount
    | Unique
    | PerParentCount
    | ValueIn
    | InRange
    | FieldPresent
    | FieldAtMost
    | ExactRows
    | OutputRows
    | WholeNumber
    | SeedIs
    | Repeatable,
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


def _declared_seed(work: Path) -> str | None:
    try:
        return parse_xml_file(work / PROJECT_ENTRY_PATH).get("rngSeed")
    except (OSError, etree.XMLSyntaxError, DTDForbiddenError):
        return None


def _copy(project: Path, case: str, destination: Path, fixtures: str = _FIXTURES) -> Path:
    """A private copy, with the case's ``fixtures`` directory laid over ``fixtures/`` so the agent cannot change it."""
    # output/ holds files from the agent's own runs; only the oracle runs may write there. casefold: macOS file
    # systems ignore case, so the engine writes into a shipped Output/ too.
    shutil.copytree(project, destination, ignore=lambda _, names: [n for n in names if n.casefold() == "output"])
    source = CASES / case / fixtures
    if source.is_dir():
        shutil.copytree(source, destination / _FIXTURES, dirs_exist_ok=True)
    return destination


def child_env(**extra: str) -> dict[str, str]:
    """The few variables a child process gets: the operator's other variables can hold secrets."""
    return {key: os.environ[key] for key in _ENV_KEYS if key in os.environ} | {"PATH": _SYSTEM_PATH} | extra


def _start(work: Path, hash_seed: str) -> subprocess.Popen[str]:
    """The project's scripts are untrusted code: the run sees its copy as the cwd and none of the operator's secrets."""
    return subprocess.Popen(
        # -P: the cwd is the project copy, and a module there must not replace the capture code
        [sys.executable, "-P", "-m", "benchmarks.authoring_eval.capture", str(work)],
        cwd=work,
        env=child_env(PYTHONPATH=str(REPO_ROOT), PYTHONHASHSEED=hash_seed),
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )


def _finish(process: subprocess.Popen[str]) -> Capture:
    try:
        stdout, _ = process.communicate(timeout=_RUN_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        process.kill()
        process.communicate()
        return Capture(error="Timeout")
    try:
        return Capture.model_validate_json(stdout)
    except ValueError:  # the interpreter died before it printed a result
        return Capture(error="CaptureCrashed")


def _observe(case: str, project: Path, changed_fixtures: list[str]) -> Observed:
    """Build one copy while the other copies run at the same time, each in its own interpreter: two runs with the
    case fixtures, and one run for each changed fixtures directory."""
    with tempfile.TemporaryDirectory() as scratch:
        root = Path(scratch)
        build_copy, first_copy, second_copy = (_copy(project, case, root / name) for name in ("build", "1", "2"))
        # numbered like the main copies: a project that reads its path must not tell the changed run apart
        changed_copies = [
            _copy(project, case, root / str(number), name) for number, name in enumerate(changed_fixtures, start=3)
        ]
        processes = [
            _start(first_copy, _HASH_SEEDS[0]),
            _start(second_copy, _HASH_SEEDS[1]),
            *(_start(copy, _HASH_SEEDS[0]) for copy in changed_copies),
        ]
        build = create_authoring_application(build_copy, descriptor_path=PROJECT_ENTRY_PATH).build()
        build_note = None if isinstance(build, ReadyBuild) else f"Build {build.outcome} in phase {build.phase.value}"
        first, second, *changed = [_finish(process) for process in processes]
        outputs = {_FIXTURES: Output(first.error, json_outputs(first_copy))} | {
            name: Output(capture.error, json_outputs(copy))
            for name, copy, capture in zip(changed_fixtures, changed_copies, changed, strict=True)
        }
        return Observed(
            build_note,
            first.error,
            first.rows,
            outputs,
            declared_seed=_declared_seed(first_copy),
            second_rows=second.rows,
            second_error=second.error,
        )


def evaluate(case: str, project: Path) -> Verdict:
    spec = OracleSpec.model_validate_json((CASES / case / "oracle.json").read_text(encoding="utf-8"))
    changed = sorted({c.fixtures for c in spec.checks if isinstance(c, OutputRows) and c.fixtures != _FIXTURES})
    observed = _observe(case, project, changed)
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
