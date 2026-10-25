# Single-line log records review (PR #384, #375)

**Accepted within the local architecture review scope.** Reviewer: Astra (independent Opus 5.5 review agent, delegated by Alex).

- Scope: `fix/log-line-breaks`, rebased onto development `afda44ba` (#383 and #386 merged), head `8f2df8c8`. The code is unchanged from the reviewed `9e21a185`.
- This review rebinds the [#383 receipt](pr-383-include-budget-and-properties-review.md) and keeps all of its assessments.
- It does not authorize a merge.

## Binding

- **Moved:** the Source and Validation digests. Validation moves through coverage counts only (13,443 calls analysed on the rebased base).
- **Unchanged:** Contract (`c70eaaf6`), analyzer, the Unknowns digest, the 313 UNKNOWN records and the 20 diagnostics.
- **Measurements:** 1,424 unresolved calls, 182 typing positions, 255 unknown positions, 0 violations.

## Source review

**The fix.** `_SingleLineFormatter.formatMessage` escapes the message part of every record:
- CR becomes `\r`;
- every other `str.splitlines()` boundary becomes `\n`: `\n`, `\v`, `\f`, `\x1c`-`\x1e`, `\x85`, U+2028, U+2029.

**History.** At 96fe276d only `\n` and `\r` were escaped. A descriptor value containing `&#x2028;` still forged a CONTROL line for a reader that splits with `splitlines()`.

**Probes at 9e21a185.**
- 11 records, one per separator plus `\r\n`, give 11 physical lines, and none starts with `CONTROL`.
- A genuine `kind=policy` record passes unchanged.
- `datamimic run` with a forged `source=` using `&#10;` or `&#x2028;` leaves no forged line on stderr.

**Coverage.**
- `setup_logger` is the only logging configuration, for MAIN and for workers, and both now use the formatter.
- `datamimic_ce` has no `basicConfig`, no other formatter and no other handler.
- Every logger is `DATAMIMIC`, with `propagate=False`.

**No double escaping.** #374 already removes every whitespace character from the policy record's `stmt`. The other CONTROL fields are static strings or type names.

**Tracebacks.** `exc_text` and `stack_info` are appended after `formatMessage`, so they stay multi-line.

### Residuals (out of scope; named in the PR text)

- **Low: a traceback can still carry a column-0 line.** An exception message that holds descriptor text with a line break still prints a column-0 continuation line inside the traceback. The runner logs user errors without a traceback.
- **Low: the CLI error line is not escaped.** `interfaces/cli/presenter.py:55` echoes `Error: <message>` unescaped to stdout. That matters only when stdout and stderr are merged.
- **Guidance:** consumers should anchor on the logger prefix.

## Evidence boundary

**LOCAL VERIFIED (by this reviewer):**
- Source review.
- The logger separator matrix.
- The CLI run probes.
- The repository-wide handler and formatter grep.
- `test_log_single_line` and `test_runtime_control_events`: 13 passed.
- ruff.
- Native collection and the strict completion gate.

**NOT VERIFIED:**
- Full suites, and mypy at this head. The coordinator reports both clean.
- CI.
