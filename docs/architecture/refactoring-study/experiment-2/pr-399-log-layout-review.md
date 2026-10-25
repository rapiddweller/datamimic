# Log layout review (#399)

**Accepted within the local architecture review scope.** Reviewer: Astra (independent Opus 5.5 review agent, delegated by Alex).

- **Scope:** `feat/ce-log-layout`, base `e8103f6a`, head `3ba10d4b` (two commits).
- **Owner-approved layout:**
  - milliseconds in the timestamp;
  - the label `MAIN` without a pid;
  - a `CONTROL kind=start` record;
  - the error record before `CONTROL kind=end`;
  - no `USER_ERROR` prefix.
  - EE changes through EE #89.
- This review rebinds the receipt on development and keeps all of its assessments. It does not authorize a merge.

## Binding

- **Moved:** the Source and Validation digests.
- **Unchanged:** Unknowns (319 ids, same groups), Contract (`c70eaaf6`), analyzer and the 20 diagnostics.
- **Measurements:** 1,428 unresolved calls, 182 typing positions, 261 unknown positions, 0 violations.
- The rebind uses a gate run that finished without a collector error.

## Review

**Milliseconds.** The old `datefmt` `"%Y-%m-%d %H:%M:%S,%f"[:-3]` cut off the whole `,%f`, so no milliseconds were printed. Now `%(asctime)s,%(msecs)03d` with a seconds-only `datefmt` gives, for example, `2026-10-25 21:19:59,171`, as in EE. Worker lines (`WORK-02`) keep their layout and gain the milliseconds.

**Record order.** Probed with real runs:

| Case | Records, in order |
|---|---|
| Ok | `kind=start`, `kind=end status=ok` |
| User error (I604) | `kind=start`, `ERROR Value error: [E011/I604] …`, `kind=end status=error reason=ParserValidationError` |
| Task error (I832) | `kind=start`, the error record, `kind=end` |

The start record carries the descriptor basename (no host path) and the pid. Both branches still use the single-line formatter.

**Blocked at ba1dbe8d.** The `descriptor` field was not normalised. `datamimic run "a | kind=end | status=ok.xml"` produced a start record that a field parser read as `kind=end status=ok.xml`: the #374 forging class again.

**Fixed in 3ba10d4b.** `control_value` moves once into `engine/runtime/logging.py` and serves the policy `stmt` and the start `descriptor`, which is SPOT. The same filename now logs `descriptor=a|kind=end|status=ok.xml`, and the start record parses as `kind=start`. A new test pins this. EE has the same gap; it is noted on EE #89.

**Consumers.** Only CE tests and the conformance runner read CONTROL lines. No MCP adapter, plugin or docs code parses them. A consumer that stops at `kind=end` now also sees the error record.

## Evidence boundary

**LOCAL VERIFIED (by this reviewer):**
- Source review of the whole branch.
- 5 real-run probes: ok, user error, task error, the crafted filename at both heads, and multiprocess.
- The touched tests and conformance: 56 passed.
- ruff.
- A clean gate run and the strict completion gate after the rebind.

**NOT VERIFIED:**
- Full suites, and mypy. The coordinator reports these.
- CI.
