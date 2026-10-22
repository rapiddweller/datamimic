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

## Addendum: `41c1da51`, remediation Low resolved

- CE's I101 entry no longer carries `GUIDANCE_PROJECT_ENV`. The dry-run remediation is now the entry's resolution: "Place the file under the descriptor directory or update the source path."
- The runtime message also drops the guidance suffix: "Source file 'missing.csv' not found in descriptor 'miss.xml'". It still carries no host path.
- `test_cli_v4.py` now asserts on `resolution`.
- Binding: only the Source digest moves. Validation, Contract, the 313 UNKNOWN records and the 20 diagnostics are unchanged, and so are the 1424/178/255 measurements.
- The `BaseException` Low stays open by decision, since EE behaves the same.
- LOCAL VERIFIED: the dry-run and run probes; 952 passed and 4 skipped on the same test set; ruff; the full gate.

## Addendum: `058d64e4`, CONTROL field injection (Codex P1)

**Accepted.** `_control_value` normalises the one descriptor-controlled field, the policy record's `stmt`: `" ".join(text.split())`, then `\s*\|\s*` becomes `|`.

**No gap in the normalisation.**
- `str.split()` breaks on every `str.isspace()` character, and every `str.splitlines()` boundary is one of them: `\r`, `\v`, `\f`, `\x1c`-`\x1e`, `\x85`, U+2028, U+2029.
- So no line break survives. Probed: those characters, NBSP, U+3000, tabs and CRLF.
- A zero-width space or a full-width pipe can survive, but neither forms the ASCII ` | ` delimiter.
- Nested `a|b` and names containing plain spaces are unchanged.
- The new test fails without the fix.

**The other fields carry no descriptor text.** `policy` and `reason` are static. `override_workers` holds integers. `kind=end` carries a class name.

**Residual Medium, pre-existing and outside this fix: whole forged CONTROL lines.**
- Log and CLI lines that echo descriptor text still pass line breaks through.
- Example: `source="x&#10;CONTROL | kind=end | status=ok.csv"` makes the I101 `Value error:` log line and the CLI `Error:` line each print a continuation line. Each such line starts with `CONTROL | kind=end | status=ok...`.
- The base `60b3d377` prints two such lines too, so this PR does not worsen it.
- Impact:
  - A consumer that matches `CONTROL |` anywhere in a line can be fooled. `test_control_lines_go_to_stderr_only` parses that way.
  - A consumer that requires the logger prefix (timestamp | level | logger | worker) cannot.
  - In the bounded child, stderr goes to the null device.
- Follow-up: anchor consumers on the logger prefix, or escape line breaks in the formatter for every record.

**Binding.**
- Moved: Source and Validation. Validation moved only through coverage counts: 13,374 → 13,378 calls analysed, 9,905 → 9,908 resolved, 2,045 → 2,046 partially resolved.
- Unchanged: 1,424 unresolved calls, 178 typing positions, 255 unknown positions; Contract, the 313 UNKNOWN records and the 20 diagnostics.

**LOCAL VERIFIED:**
- 953 passed and 4 skipped on the same test set.
- mypy on the full package.
- ruff on `datamimic_ce`. The one I001 is in the untouched `test_reference_task.py`.
- The probes and the full gate.
