# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Blind-agent eval oracle (#412): judge a project by the rows it produces, never by its own acceptance file.

    python -m benchmarks.authoring_eval.oracle <case-id> <project-dir>

Builds the project, runs it, captures the rows per product and evaluates ``cases/<id>/oracle.json``. The verdict
is JSON with one reason per check and never contains a row value."""

import argparse
import contextlib
import filecmp
import json
import os
import re
import secrets
import shutil
import signal
import subprocess
import sys
import tempfile
from abc import ABC, abstractmethod
from collections import Counter
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import IO, Annotated, Literal

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
    products: frozenset[str] = frozenset()  # the products the run captured


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
    edited_fixtures: tuple[str, ...] = ()  # the supplied fixture files that the project changed or deleted


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


class UniqueTogether(_Check):
    """No two rows hold the same combination of the fields; one field alone may repeat."""

    kind: Literal["unique_together"]
    product: str
    fields: list[str]

    def label(self) -> str:
        return f"unique_together:{self.product}.{'+'.join(self.fields)}"

    def failure(self, observed: Observed) -> str | None:
        rows = _product_rows(observed, self.product)
        if isinstance(rows, str):
            return rows
        combinations = [tuple(row.get(name) for name in self.fields) for row in rows]
        if not all(isinstance(value, str | int | float) for combination in combinations for value in combination):
            return "values are missing or not scalar"
        repeated = len(combinations) - len(set(combinations))
        return None if not repeated else f"{repeated} duplicate combinations"


# date.fromisoformat also reads 20260301 and 2026-W09-7; the prompts ask for YYYY-MM-DD only
_ISO_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


def _iso_date(value: object) -> date | None:
    """The date of a YYYY-MM-DD text; None for anything else, a null and an empty text included."""
    if not isinstance(value, str) or _ISO_DATE.fullmatch(value) is None:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:  # 2026-02-30
        return None


def _typed(value: object) -> str:
    """A value with its JSON type, so that 1, "1", 1.0 and true stay different."""
    return json.dumps(value, sort_keys=True, default=str)


class DateWindow(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    date: str  # the field of the checked row
    start: str  # the fields of the target row that bound it; both days count
    end: str


class RowExistsIn(_Check):
    """For each row of ``product`` a row of ``target`` holds the same ``fields`` with the same JSON types. With a
    window, the date of the row is also from the target's start to its end, both days included. A bound that is
    missing, null or not a YYYY-MM-DD date never matches: no expiry date is no validity."""

    kind: Literal["row_exists_in"]
    product: str
    target: str
    fields: list[str]
    window: DateWindow | None = None

    def label(self) -> str:
        return f"row_exists_in:{self.product}->{self.target}"

    def _key(self, row: Row) -> tuple[str, ...] | None:
        if any(name not in row for name in self.fields):
            return None
        return tuple(_typed(row[name]) for name in self.fields)

    def _covers(self, target: Row, row: Row) -> bool:
        if self.window is None:
            return True
        day, start, end = (
            _iso_date(r.get(f))
            for r, f in ((row, self.window.date), (target, self.window.start), (target, self.window.end))
        )
        return day is not None and start is not None and end is not None and start <= day <= end

    def failure(self, observed: Observed) -> str | None:
        rows, targets = _product_rows(observed, self.product), _product_rows(observed, self.target)
        if isinstance(rows, str):
            return rows
        if isinstance(targets, str):
            return targets
        by_key: dict[tuple[str, ...], list[Row]] = {}
        for target in targets:
            if (key := self._key(target)) is not None:
                by_key.setdefault(key, []).append(target)
        unmatched = 0
        for row in rows:
            key = self._key(row)
            if key is None or not any(self._covers(target, row) for target in by_key.get(key, [])):
                unmatched += 1
        return None if not unmatched else f"{unmatched} of {len(rows)} rows have no matching {self.target} row"


class DateRange(_Check):
    """Every value is a YYYY-MM-DD text from ``min`` to ``max``, inclusive, except exactly ``missing`` nulls. An
    empty text is not a null, and a row without the field fails."""

    kind: Literal["date_range"]
    product: str
    field: str
    min: date
    max: date
    missing: int = 0

    def label(self) -> str:
        return f"date_range:{self.product}.{self.field}"

    def failure(self, observed: Observed) -> str | None:
        found = FieldRef(product=self.product, field=self.field).values(observed)
        if isinstance(found, str):
            return found
        nulls = sum(value is None for value in found)
        if nulls != self.missing:
            return f"{nulls} values are null, expected {self.missing}"
        bad = [v for v in found if v is not None and not ((day := _iso_date(v)) and self.min <= day <= self.max)]
        return None if not bad else f"{len(bad)} values are not dates YYYY-MM-DD in {self.min}..{self.max}"


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


class Text(_Check):
    """Every value is a text that is not empty; a number is not a text."""

    kind: Literal["text"]
    product: str
    field: str

    def label(self) -> str:
        return f"text:{self.product}.{self.field}"

    def failure(self, observed: Observed) -> str | None:
        found = FieldRef(product=self.product, field=self.field).values(observed)
        if isinstance(found, str):
            return found
        bad = [value for value in found if not isinstance(value, str) or not value]
        return None if not bad else f"{len(bad)} values are not texts that are not empty"


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
    ignore_extra_fields: bool = False  # True: compare only the fields that ``rows`` names

    def label(self) -> str:
        return f"exact_rows:{self.product}"

    def failure(self, observed: Observed) -> str | None:
        found = _product_rows(observed, self.product)
        if isinstance(found, str):
            return found
        if self.ignore_extra_fields:
            named = {key for row in self.rows for key in row}
            found = [{key: value for key, value in row.items() if key in named} for row in found]
        return _row_difference(found, self.rows)


class OutputRows(_Check):
    """A run with the case directory ``fixtures`` laid over ``fixtures/`` wrote ``<product>.json`` (the JSON
    exporter) holding exactly ``rows``. A changed fixtures directory proves that the rows come from the input.
    With a chunk size, the exporter writes ``<product>_<n>.json`` parts; the check collects all of them. Row order
    does not matter. A file whose stem names another product is not a part of this product."""

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
        if self.product not in output.products:
            return f"product {self.product} was not produced"
        name = re.compile(re.escape(self.product) + r"(?:_\d+)?")
        # a product named priced_orders_0 also writes priced_orders_0.json, which is not a part of priced_orders
        rows = [
            row
            for stem, part in output.files.items()
            if name.fullmatch(stem) is not None and (stem == self.product or stem not in output.products)
            for row in part
        ]
        if not rows:
            return f"no {self.product}.json was written"
        return _row_difference(rows, self.rows)


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


class FixturesUnchanged(_Check):
    """Every file that the case supplies in ``fixtures/`` is in the project, byte for byte. A new file is allowed."""

    kind: Literal["fixtures_unchanged"]

    def label(self) -> str:
        return "fixtures_unchanged"

    def failure(self, observed: Observed) -> str | None:
        edited = observed.edited_fixtures
        return None if not edited else f"supplied fixtures changed or deleted: {', '.join(edited)}"


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
    | UniqueTogether
    | RowExistsIn
    | DateRange
    | PerParentCount
    | ValueIn
    | InRange
    | Text
    | FieldAtMost
    | ExactRows
    | OutputRows
    | WholeNumber
    | SeedIs
    | FixturesUnchanged
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


def _edited_fixtures(project: Path, case: str) -> tuple[str, ...]:
    """The case fixture files that the submitted project changed or deleted. Read before any copy gets the overlay."""
    source = CASES / case / _FIXTURES
    edited = []
    for path in sorted(source.rglob("*")):
        submitted = project / _FIXTURES / path.relative_to(source)
        if path.is_file() and not (submitted.is_file() and filecmp.cmp(path, submitted, shallow=False)):
            edited.append(path.relative_to(source).as_posix())
    return tuple(edited)


def child_env(**extra: str) -> dict[str, str]:
    """The few variables a child process gets: the operator's other variables can hold secrets."""
    return {key: os.environ[key] for key in _ENV_KEYS if key in os.environ} | {"PATH": _SYSTEM_PATH} | extra


def wait_then_kill_group(process: subprocess.Popen[bytes], timeout: float) -> int | None:
    """The exit code, or None on a timeout. Every process left in the group of ``process`` (started with
    ``start_new_session=True``) ends with it. A process that calls setsid() leaves the group and is out of reach."""
    try:
        return process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        return None
    finally:
        # EPERM: macOS refuses the signal while the members of the group exit (#432)
        with contextlib.suppress(ProcessLookupError, PermissionError):
            os.killpg(process.pid, signal.SIGKILL)
        process.kill()  # the leader at least, when killpg was refused; a no-op after a normal exit
        process.wait()


def _start(work: Path, hash_seed: str) -> tuple[subprocess.Popen[bytes], IO[bytes]]:
    """The project's scripts are untrusted code: the run sees its copy as the cwd and none of the operator's secrets.
    Stdout goes to a file, not a pipe: a descendant that keeps a pipe open blocks the read until it exits."""
    stdout = tempfile.TemporaryFile()  # noqa: SIM115 - _finish closes it
    process = subprocess.Popen(
        # -P: the cwd is the project copy, and a module there must not replace the capture code
        [sys.executable, "-P", "-m", "benchmarks.authoring_eval.capture", str(work)],
        cwd=work,
        env=child_env(PYTHONPATH=str(REPO_ROOT), PYTHONHASHSEED=hash_seed),
        stdout=stdout,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    return process, stdout


def _finish(process: subprocess.Popen[bytes], stdout: IO[bytes]) -> Capture:
    with stdout:
        if wait_then_kill_group(process, _RUN_TIMEOUT_SECONDS) is None:
            return Capture(error="Timeout")
        stdout.seek(0)
        try:
            return Capture.model_validate_json(stdout.read())
        except ValueError:  # the interpreter died before it printed a result
            return Capture(error="CaptureCrashed")


def _observe(case: str, project: Path, changed_fixtures: list[str]) -> Observed:
    """Build one copy while the other copies run at the same time, each in its own interpreter: two runs with the
    case fixtures, and one run for each changed fixtures directory."""
    with tempfile.TemporaryDirectory() as scratch:
        root = Path(scratch)
        # random names: a project that reads its path must not tell the runs apart
        build_copy, first_copy, second_copy = (_copy(project, case, root / secrets.token_hex(4)) for _ in range(3))
        changed_copies = [_copy(project, case, root / secrets.token_hex(4), name) for name in changed_fixtures]
        runs = [
            _start(first_copy, _HASH_SEEDS[0]),
            _start(second_copy, _HASH_SEEDS[1]),
            *(_start(copy, _HASH_SEEDS[0]) for copy in changed_copies),
        ]
        build = create_authoring_application(build_copy, descriptor_path=PROJECT_ENTRY_PATH).build()
        build_note = None if isinstance(build, ReadyBuild) else f"Build {build.outcome} in phase {build.phase.value}"
        first, second, *changed = [_finish(*run) for run in runs]
        outputs = {_FIXTURES: Output(first.error, json_outputs(first_copy), frozenset(first.rows))} | {
            name: Output(capture.error, json_outputs(copy), frozenset(capture.rows))
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
            edited_fixtures=_edited_fixtures(project, case),
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
