# Missing-source error and CONTROL events review (#271, #272)

**Accepted within the local architecture review scope.** Reviewer: Astra (independent Opus 5.5 review agent, delegated by Alex).

- Scope: `feat/portable-missing-source-error`, base `60b3d377` (origin/development), head `37a8e92c` (two commits).
- This review rebinds the [#372 receipt](pr-372-actionable-remediations-review.md) and keeps all of its assessments.
- It does not authorize a merge.

## Binding

- **Moved:** Source and Validation digests. The new values are in `completion-unknowns.json`.
- **Unchanged:** Contract (`c70eaaf6`), analyzer, the 313 UNKNOWN records (same ids, same digest) and the 20 `interface.usage_unknown` diagnostics.
- **Measurements equal the base:** 1,424 unresolved calls, 178 typing positions, 255 unknown positions, 0 violations.

## Source review

**Correctness.**
- `MissingSourceError(InvalidSourceError, FileNotFoundError)` keeps every existing `except FileNotFoundError` caller working (dataset fallbacks in `domains/**`, `engine_check.py:55`), while `UserErrorBase` handling now takes the portable path.
- `invalid_source_error` returns the subclass only for `SOURCE_FILE_NOT_FOUND`, by enum identity. The dry-run restore allow-list carries the new type, so the child payload restores it.
- I101 `SOURCE_FILE_NOT_FOUND` exists in datamimic-ee (`datamimic_ee/errors/catalog/codes.py:42`); CE codes stay a subset of EE codes. The CE template omits EE's "in task workspace", which is correct for CE.
- The CONTROL grammar matches EE exactly: `kind=end | status=ok|error | reason=<type name>` (`execution_session.py:142,157`, `progress.py:263`) and `kind=policy | policy | stmt | override_workers=a -> b | reason` (`progress.py:218`). `stmt` is the full name, joined by `|` without spaces, so the ` | ` field separator still parses.
- Each public entry (CLI, Python interfaces, factory, bounded child) opens one session per run, so one `execute()` yields one `kind=end` line.

**Redaction.**
- The reader message carries `file_path.name` only. The native `FileNotFoundError` survives as `__cause__` and is not rendered.
- Probe, `datamimic run` with a missing `sub/missing.csv`: the host path appears 3 times on the base (message plus traceback) and once on the head, the pre-existing "Current working directory" INFO line. The head prints no traceback for this error.
- Probe, `authoring dry-run` (CSV and JSON): no host path in stdout or stderr; `ce_error.issue_code == "I101"`.
- `reason=` is a class name, never a value.

**`kind=end` in the bounded child: harmless, not noise.**
- `session.execute()` runs inside `_suppress_worker_stderr()` (`dryrun.py:1165`), which points fd 2 at the null device. The package defines no file handler.
- Probe: zero CONTROL lines in dry-run stdout or stderr for an ok and a failing descriptor.
- Cost: one INFO record per run. The `status=ok` line is emitted only after `SetupTask.execute()` returns.

**Over-engineering.** None. One subclass that earns its place (catch compatibility plus catalog identity), one factory branch, three log lines. No `kind=start`, in line with YAGNI.

### Findings (not P1; follow-ups)

**Low: the dry-run remediation for a missing file got less actionable** (`errors/catalog/source_errors.py`, the new I101 entry; `dryrun.py:177`).
- Base: "Provide the referenced resource relative to the descriptor workspace."
- Head: `GUIDANCE_PROJECT_ENV`, "Check your project environment configuration or uploaded assets." That is Platform wording that a CE agent cannot act on.
- Cause: `issue.guidance or issue.resolution` takes the guidance first, so I101's own resolution loses: "Place the file under the descriptor directory or update the source path."
- The new `test_cli_v4.py` assertion pins `remediation == guidance`, so it locks in the weaker text.
- Fix: drop `guidance` from CE's I101 entry and assert on `resolution`. Template parity with EE is already relaxed.

**Low: no end event for `BaseException`.** A `KeyboardInterrupt` or `SystemExit` passes through `execute()` without a `kind=end` line. "One end event per run" therefore holds for `Exception` only. This matches EE.

## Evidence boundary

**LOCAL VERIFIED (by this reviewer):**
- Source review and the EE parity checks above.
- Tests: 952 passed and 4 skipped, across the changed tests, `test_authoring` and `test_composite_reference`.
- Redaction probes against the base and the head.
- ruff, and mypy on the full package.
- Native collection and the strict completion gate.

**NOT VERIFIED:**
- Full suites.
- CI.
- Windows.
