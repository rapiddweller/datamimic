# Source file errors review (PR #392, #379)

**Accepted within the local architecture review scope.** Reviewer: Astra (independent Opus 5.5 review agent, delegated by Alex).

- Scope: `fix/source-file-errors`, base `cbecf0a6` (#384 merged), head `dd22611b` (two commits).
- This review rebinds the [#384 receipt](pr-384-log-line-breaks-review.md) and keeps all of its assessments.
- It does not authorize a merge.

## Binding

- **Moved:** the Source and Validation digests. Validation moves through coverage counts only (13,448 calls analysed).
- **Unchanged:** Contract (`c70eaaf6`), analyzer, the Unknowns digest, the 313 UNKNOWN records and the 20 diagnostics.
- **Measurements:** 1,424 unresolved calls, 182 typing positions, 255 unknown positions, 0 violations.

## Review

**Error mapping in `readers.py`.**

| Source failure | Now |
|---|---|
| Missing XML, XLSX, DbUnit or fixed-width file | I101 (`MissingSourceError`, file name only) |
| Malformed XML | I105, cause `ExpatError` |
| Text-only `<item>` | I105, static guidance |
| JSON value outside the data model | I104 |
| Invalid XLSX, fixed-width file without a spec | Messages name the file only, no code |

No new codes. I101, I104 and I105 exist in EE under the same names.

**Blocked at fa81b220, then fixed.** I105's `ExpatError` cause did not cross the bounded-child boundary: the payload decoder refused it as an unsupported global. Dry-run and Build therefore reported "Bounded child returned invalid capture evidence" with no code.

dd22611b adds `ExpatError` to the `_decode_worker_payload` allow-list, next to `JSONDecodeError`. It is a plain `Exception` subclass. A CLI dry-run test now pins I105.

**Re-probed with dry-run:**
- Malformed XML: I105.
- Text-only `<item>`: I105.
- Missing XML: I101 at `…/generate/source`.
- Invalid XLSX: a generic child failure with no code, as intended.
- No host path appears in any output.

**Absolute paths.** The cached CSV shape message now names the file only. What remains is not diagnostic text: `cache.py:30` (the cache key) and a debug log line.

**Callers.**
- Nothing in `datamimic_ce` catches `ExpatError`.
- `InvalidSourceError` is a ValueError subclass, so existing `except ValueError` paths still apply.
- The remaining text pins still match.

### Finding (not P1)

**Low: the extra guidance stops at the runtime message.** The static `guidance=` given for the text-only `<item>` and the JSON data-model cases appears only in the runtime message. The dry-run and Build remediation use the catalog's I104/I105 guidance, which is Platform-worded (`GUIDANCE_PROJECT_ENV`). This is an optional follow-up, and the PR text names it.

## Evidence boundary

**LOCAL VERIFIED (by this reviewer):**
- Source review.
- A nine-case dry-run and run probe at fa81b220, and the four dry-run re-probes at dd22611b.
- A pickle decode probe.
- A base comparison.
- 92 targeted tests passed: `test_source_reader_errors`, `test_cli_v4`, `test_data_source_length_source_spot` and `test_portable_errors`.
- ruff.
- Native collection and the strict completion gate.

**NOT VERIFIED:**
- Full suites, and mypy at this head. The coordinator reports both clean.
- CI.
