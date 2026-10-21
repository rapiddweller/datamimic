# Bounded write containment architecture review (issue 361, PR #362)

**Accepted within the local architecture review scope.** Reviewer: Astra (independent Opus 5.5 review agent, delegated by Alex).

- Scope: `fix/bounded-write-containment`, base `29fb4da8` (merged #360), head `5abd63a2` (`114c00bd`, `280a6e02`, `49c12a3b`, `a5b7f0c3`, `5abd63a2`, `f27d0d9e`, `5a383526`).
- This review rebinds the [issue 332 receipt](issue-332-bounded-python-library-review.md) and keeps all of its assessments.
- It does not authorize a merge. It does not claim that the containment is a sandbox or that every native rule passes.

## Current binding

| Item | Value |
|---|---|
| Source | `0b16f3b846168a710e642dd4e228433b7504416f817e061e5c4269c040a2a402` |
| Target (unchanged) | `d83d4df102a2588a54598e26cb045b721cb024a118f51e31592b135050d4e78e` |
| Analyzer (unchanged; ArchKeel 4.0.1, Python 3.11.12) | `bb1a3262d3fdd38c3e9a6af980cc063281ae98ab1c28c89c2c5be6dfb450744f` |
| Validation | `5bbdcdb4f458e4e2e70cd9539459fd5b173e0935657274d00fbf27cc8fb4c22c` |
| UNKNOWN | `1a60ffbf787f02675d9769721e4178c2a2070bd98a038aca3baddd69b01b50b2` |

**Budgets:**
- `calls_unresolved` is ratcheted **down** from 1,431 to the measured 1,429 in `known-violations.json`. That is the only change in that file. It tightens the budget and authorizes nothing; `measurement_amendment` says so.
- `typing_positions` stays at 178 and `unknown_positions` at 256.
- No contract, gate or other policy change.

## Design

The bounded child already runs in a private temporary root, with the workspace snapshot below it.

When `allow_side_effects` is false, `_contain` (`bounded_executor_child.py:52`) installs one audit hook (`:83`) for the rest of the child process. It does four things:
- **Writes:** refuses writing opens and the listed path events (`:28`) unless the target resolves inside the private root.
- **Checked files:** refuses writes to the files the snapshot held at start, so a later library or resource cannot be replaced after it was checked.
- **Transport files:** refuses writes to the request, reply and staging files until the child clears that guard just before writing its own reply (`:113`, `:130`).
- **Processes:** refuses the listed process-start events (`:23`).

Python's `tempfile` is redirected into the private root. Refusals are plain `PermissionError`s, and the authoring projection maps them to a static containment hint (`dryrun.py:152`, `:169`, `:179`).

This is the smallest placement that works: one function in the child, with no new component or port, and no change to the engine.

## Findings across the review rounds

**280a6e02 (blocked), fixed in 49c12a3b:**
- Process events missing from the list (`os.forkpty`, `os.startfile`) were added.
- Extended-attribute and flag path events were added.
- The null device now matches both spellings (`:71`). That addresses the likely Windows cause of the child dying before its reply.
- A native-code refusal now reaches the parent: `SystemError` is on the passive unpickler allowlist (`dryrun.py:845`).
- The run can no longer overwrite its own transport files.

**Confirmed limit:** I verified independently that CPython 3.11.12 and 3.13.3 raise no audit event for `os.mkfifo` or `os.mknod`. An audit hook cannot refuse them, and the code comment documents this. On Linux an unprivileged `mknod` can also create an empty regular file. Neither carries data.

**a5b7f0c3:** dropping the `TMPDIR`/`TEMP`/`TMP` environment assignments is acceptable.
- Python's `tempfile` is the engine's temp writer.
- Child processes are refused.
- Native code is outside the audited scope in any case.

**Info:**
- `shutil.copyfile`/`copytree` also refuse a snapshot file used as the copy source. No library or expression path reaches this, and the engine tests pass.
- Engine `.pyc` writes refused after the hook are skipped by `importlib`, and the import still succeeds (verified).

**5abd63a2 (Codex threads), accepted:**
- Writes are now refused when they resolve against a directory descriptor that the audit event does not name. Specifically:
  - a relative `os.open` write;
  - a relative path in a path event that carries a real `dir_fd`.
- The engine opens absolute paths, and smoke-export cleanup (a relative remove without `dir_fd`) still passes. The conservative refusal of relative `os.chown`/`os.setxattr` is acceptable.
- The snapshot now also holds directories and the workspace root, so a renamed checked directory cannot be rewritten unseen.
- On POSIX, `os.mkfifo`/`os.mknod` are replaced by typed refusals.

**Architectural judgement on that replacement:** acceptable.
- The child is a dedicated, single-purpose process.
- The replacement is installed only together with the hook, so only when side effects are not allowed.
- It needs no type ignore.
- Its ceiling is honest: it covers lookups through the `os` module attribute, which is the route DSL expressions use (libraries cannot import `os`). Like the hook, it is not a sandbox. The comment and the receipt's `delivery_boundary` state this.

**f27d0d9e (Codex threads), accepted:**
- The null-device exception now applies only to writing opens, so audited path operations on the null device are refused.
- File-descriptor forms of the audited path events are refused.

Engine check:
- No bounded engine path uses a file-descriptor form. A search of `datamimic_ce` finds no `fchmod`, `ftruncate`, `copystat`, `copymode` or `chown`. `shutil.copy2` appears only in the demo installer.
- Under an audit logger, an openpyxl XLSX save, a JSON write with `file.truncate()` (the JSON exporter's call), a `tempfile` write, `shutil.copyfile` and a SQLite write raised none of the audited path events.
- Smoke export for all six file exporters still passes.

**5a383526 (Codex thread), accepted:** a relative path is now refused when any non-negative integer follows the first path, which is where a directory descriptor appears.
- I recorded the audit argument shapes with a real `dir_fd`. In every case the descriptor lies in `args[1:]`: `os.remove`, `os.rmdir` and `shutil.rmtree` (second), `os.mkdir`, `os.chmod` and `os.symlink` (third), `os.rename` and `os.link` (third and fourth), `os.utime` (fourth).
- `os.chown` (path, uid, gid, dir_fd) has the same shape by signature. `os.truncate`, `os.chflags`, the xattr events and the `shutil` copy/move events take no `dir_fd`.
- No dir_fd shape in `_PATH_EVENTS` is left uncovered.
- The conservative cost (a relative `mkdir`/`chmod`/`truncate` with an explicit mode or length is refused) does not affect the engine. Smoke export, including its relative cleanup with `dir_fd` -1, passes.

**On the proposed docstring note:** appropriate if it names the scope (accidental Python-level writes and process starts, not a sandbox) and the concrete follow-up issue number, rather than a generic "outstanding reports" sentence. One line is enough; the scope line below is the reference.

No blocking finding at `5a383526`.

## Scope line (binding for future threads)

The containment keeps **accidental** Python-level writes and process starts of a bounded run inside its private root.

**Out of scope, and documented:**
- native code outside audited calls;
- `os.mkfifo`/`os.mknod` beyond the replaced `os` attributes;
- network access;
- races by threads inside the child.

It is not a security sandbox. Real isolation would be OS-level, as a separate decision for Alex.

## Windows

Reasoned from code only. CI on `windows-latest` is the evidence.
- Path comparison uses `normcase(realpath(...))` for both the private root and the target. Short names and a different drive do not create false matches.
- `os.walk` of the snapshot ignores errors.
- Refused `.pyc` writes and `platform` helpers catch `OSError`.
- I found nothing else in `_contain` that would end the child before its reply.

**NOT VERIFIED on Windows.**

## Redaction and hints

- The refusal texts and `_CONTAINMENT_HINT` are static.
- `_decode_reply` now uses the worker's `fix_hint` for untyped failures (`bounded_executor.py:223`). That hint comes only from static texts, catalog texts or `DomainError.hint`, which carries dataset vocabulary and is already shown on the typed path. No descriptor value reaches it.

## Native result

- **Base:** I re-collected `29fb4da8` independently, and it reproduces every digest of the previous receipt.
- **Head:**
  - 534/534 files; failures [].
  - 0 violations, 0 baseline additions or resolutions.
  - Rules: 271 PASS and 5 UNKNOWN.
  - The 20 diagnostics are identical, and the report exits 0.
- **Calls:** 13,141 → 13,190; resolved 9,695 → 9,744; partially resolved 2,015 → 2,017; unresolved 1,431 → 1,429.
  - All changes are in `bounded_executor_child.main`.
  - `reply_file.with_suffix` is removed, and `guarded.clear` is added.
  - `staging.write_bytes`/`staging.replace` move from unresolved to partially resolved.
- **UNKNOWN records:** 314, with identical identities. Only `UNKNOWN-PYTHON-DYNAMIC-CALLS` changes its count (1,431 → 1,429); the `dynamic_call_limit` assessment is updated to match.

## Evidence boundary

**LOCAL VERIFIED (by this reviewer):**
- Source review of `29fb4da8..5a383526`.
- Bounded dry-run containment probes at `280a6e02` and `49c12a3b`: outside writes and process starts refused; new files inside the workspace and the POSIX null device allowed.
- Build smoke export (CSV, JSON, XML, TXT, XLSX, DbUnit) passed together with replay at `280a6e02`; CSV/JSON/XML/TXT passed again at `49c12a3b` and XLSX/DbUnit at `a5b7f0c3`.
- Audit-event check for `mkfifo`/`mknod` on CPython 3.11.12 and 3.13.3.
- `.pyc` and `tempfile` behaviour under the hook.
- At `5a383526`: the related suites, 204 passed and 4 skipped. Smoke export with replay passed for six exporters. ruff and mypy are clean. I recorded the dir_fd argument shapes.
- At `f27d0d9e`: the related suites, 203 passed and 4 skipped. Smoke export with replay passed for six exporters. ruff and mypy are clean. The audit-event census covered exporter-like writes. Unresolved and partially resolved calls are unchanged from `5abd63a2`; only resolved calls grew (+5).
- At `5abd63a2`: the related suites plus the determinism scenarios, 201 passed and 4 skipped (I did not check which tests were skipped). Smoke export passed for all six file exporters (CSV, JSON, XML, TXT, XLSX, DbUnit) together with replay. ruff and mypy are clean. The calls profile is identical to `a5b7f0c3`.
- At `a5b7f0c3`:
  - 177 related tests passed, 4 skipped. Of the suites I ran, `test_bounded_executor_windows.py` is the only one targeting Windows, so the skips are probably Windows-only; I did not check which tests they were.
  - ruff and mypy are clean.
  - Native collection at head and base, with a decoded call diff.
  - Strict completion gate acceptance.

**Pre-existing, outside this PR:** three tests in `tests_ce/architecture` fail identically on base `29fb4da8`, and `make architecture-check` does not run them:
- two smoke-export annotation tests in `test_io_public_boundaries.py`;
- the `test_text_io_encoding_gate.py` case for `bundle.py`.

**NOT VERIFIED:**
- Windows.
- CE CI.
- Full unit and integration suites (the author reports 3,231 and 608 passed).
- External services.
