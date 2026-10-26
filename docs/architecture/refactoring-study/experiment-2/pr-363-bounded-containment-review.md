# Bounded containment: dir_fd positions and AF_UNIX binds (#363)

**Accepted within the local architecture review scope.** Reviewer: Astra (independent Opus 5.5 review agent, delegated by Alex).

- **Scope:** `fix/ce-bounded-containment-363`, base `2a8d4875`, head `d21ca356` (two commits, not pushed).
- An independent verification team reviewed the change before this review. It found a HIGH bypass: a buffer-typed AF_UNIX address. `d21ca356` closes it.
- This review rebinds the receipt on development and keeps all of its assessments. Containment remains a lint-grade guard, not a sandbox.
- It does not authorize a merge.

## Binding

- **Moved:** the Source and Validation digests.
- **Unchanged:** Unknowns (319 ids, same groups), Contract (`c70eaaf6`), analyzer and the 20 diagnostics.
- **Measurements:** 1,428 unresolved calls, 182 typing positions, 261 unknown positions, 0 violations.
- The rebind uses a gate run that finished without a collector error.

## Review

**dir_fd positions.**
- `_PATH_EVENTS` maps each event to the argument positions that carry `dir_fd`.
- I verified every mapped position with a real audit hook on CPython 3.11.12, 3.12.10 and 3.13.3. All nine events with a `dir_fd` match: `os.remove`, `os.rmdir`, `os.mkdir`, `os.chmod`, `os.symlink`, `os.rename`, `os.link`, `os.utime` and `os.chown`.
- CPython converts a non-int `dir_fd` through `__index__` before it raises the event, so the hook always sees an `int`.
- `os.link` and `os.rename` check both paths, so a hard link from an outside source is refused.

**AF_UNIX binds.**
- A tuple address (AF_INET, AF_INET6 and other families) is not a filesystem path, and it passes.
- A `str` or `bytes` address must resolve inside the private root.
- A leading NUL names a Linux abstract socket, which creates no inode, so it is skipped. This path is not tested on Linux.
- Any other non-tuple address is refused, for example a buffer or a `PathLike`.
- Over-refusing a `PathLike` address inside the root is acceptable. Typed normalisation would have raised the typing budget.

**Tests.** The DSL models in `bounded_containment_models/{accepted,refused}` get their outside paths per run. `test_bounded_containment`: 24 passed.

### Findings (Info, scope)

- **AF_UNIX `connect` is not contained.** A script can still connect to an existing UNIX socket outside the root and reach a host service through it. Refusing that would break local-socket database connections, and TCP connects are not contained either. This matches the documented scope (write containment, no processes); keep it stated.
- **C-level file access is not audited.** For example, `sqlite3.connect` creates its file in C. Bounded runs rely on the descriptor SQLite path check and on the library import check here. An extra hook for `sqlite3.connect` would be defence in depth.
- **TOCTOU.** `contained()` resolves the path when the event fires. Another thread can swap a path component for a symlink before the system call runs. This is a known limit of an audit-hook guard.
- **Known limit, commented in the code.** `shutil.rmtree` of a non-empty relative tree stays refused.

## Evidence boundary

**LOCAL VERIFIED (by this reviewer):**
- Source review.
- The audit-position probe on CPython 3.11, 3.12 and 3.13.
- `test_bounded_containment`.
- ruff.
- A clean gate run and the strict completion gate after the rebind.

**NOT VERIFIED:**
- Linux (abstract sockets) and Windows.
- Full suites and mypy. The coordinator reports these.
- CI.
