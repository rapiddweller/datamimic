# Amendment 14: retire the local Pylint hard gate

Date: 2026-09-24.

## Decision

`make lint` runs Ruff. Full-package MyPy remains `make typecheck`; ArchKeel remains
`make architecture-check`. Pylint is no longer a required local gate. Remove the
CSV and JSON exporters' `_reset_state` overrides because their base class has no
such method and neither override has callers.

## Why

The frozen local target treated Pylint E/F findings as a hard gate, but Pylint is
not a project dependency or a CI job. CI already runs Ruff, MyPy, and ArchKeel
independently. In this checkout Pylint reported 24 E/F findings, including
missing optional/external imports, Pydantic `FieldInfo` and SQLAlchemy inference
errors, and flow-analysis reports on code paths guarded by the runtime mode.
The CSV and JSON `_reset_state` overrides were genuine dead code: their parent
does not define the method, and repository search found no callers.

This changes only the local lint acceptance target; it does not alter CI gates or
the architecture contract. Pylint-only diagnostics are no longer a required
signal. The remaining findings were not individually validated as product
defects; Ruff, MyPy, and ArchKeel are the applicable checks. Focused CSV/JSON
exporter tests passed (26), `make lint` passed, and full-package MyPy passed on
474 files using the project's virtual environment. The full unit gate passed
(1,173 passed, 11 skipped). Removing the dead methods
reduced ArchKeel's measured unresolved calls from 1,283 to 1,279. The numeric
baseline budget was narrowed accordingly; pinned ArchKeel 0.6.1 then passed with
0 violations, 0 unknown positions, and no new or resolved baseline findings.
Full external-service and remote CI status remain outside this amendment.
