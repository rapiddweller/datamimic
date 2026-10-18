# Amendment 216 — Windows snapshot file identity

2026-10-18. Parent and independent Astra review approved this narrow correction
and exact measurement tightening. Amendment 215 remains the first merged-source
observation; its local architecture result did not establish Windows execution.

Windows CI exposed five pre-child ENVIRONMENT failures. Python's documented
DirEntry.stat metadata omits Windows device/inode identity, so comparing it with
opened-file identity rejected unchanged files. Snapshotting now uses fresh
os.stat with POSIX directory-fd anchoring or the Windows full path. Regular-file,
size, before/opened/after identity, retained Windows handles, reparse checks and
workspace limits remain intact. No new ownership or dependency permission.

The maintained zero-identity regression failed before the correction and passes
after it; replacement rejection also passes. Affected tests: 68 passed, four
native Windows skips. Full Ruff and MyPy (534 files) pass. Actual Windows rerun
remains a CI requirement.

## Exact native evidence

ArchKeel 3.0.1 / Python 3.11.12; analyzer digest remains
`a9e159db0a1912171ba9ec7abe8a60aac53d1e865159acfc88686bd451741ef0`.
Source digest becomes
`80d603a7c89bd305eb7964c9dcd8651dad643a141ccac4c8cb24e9b71097d1b4`;
target digest remains
`ada24d8d83e92bce0a93629d87d9c74ad248b2d306ccf2ddc64829d1c5e50438`.

Unresolved-call ceiling tightens from 1410 to the measured 1409. The sole
semantic removal is `copy_directory`'s `entry.stat` call. One added/removed
anonymous-caller pair reflects a five-line shift, giving one added/two removed
native identities overall. Complete unresolved multiset SHA256:
`69eaffb982afe20f9c1fb63503d6c8f3d11e011838fcd990aebeff00bdad67df`.
Identity and hashing are unchanged from Amendments 214–215.

Typing remains 173 with the identical multiset; cycle edges 2, private crossings
0 and untyped private accesses 0 remain unchanged. Native validation records
zero violations or coverage failures. All 298 UNKNOWN IDs remain; only the
aggregate dynamic-call count changes. No UNKNOWN becomes PASS, no headroom is
added. Completion requires the fresh independently authored source-bound receipt
and full canonical Make gate; previous receipts remain historical.

## Combined service follow-up

The Windows-only source above remains historical. The combined service source is
`0e4aa5b2819210a9abe995260c6f62ded06c4fad2078a8bf0a5a1e4949e2ec9d`.
It also restores optional SQL count preflight for typed I901 failures whose
native cause is ProgrammingError or OperationalError; policy failures still
propagate. The Oracle correction changes only the service fixture, preserving
native read-only enforcement. No ownership or permission change is required.

The same 3.0.1 reader reports zero violations, drift or measurement failures.
Call and typing multisets above are unchanged, as are ceilings 1409/173/2/0/0.
All 298 UNKNOWN IDs remain; eleven records change only evidence/fact references.
The target and analyzer digests remain unchanged. The service-stage receipt
binds that source; its acceptance is historical after the cleanup correction below.

## Cleanup exception priority follow-up

Sonar identified two returns inside executor cleanup handlers that suppressed an
active exception or cancellation. Both handlers now assign CLEANUP evidence;
the existing return outside finally preserves normal cleanup-failure reporting.
Cleanup attempts and resource safeguards remain unchanged. Four regressions fail
before the fix and pass after actual removal/reaping with injected cleanup errors.
The affected suite passes 72 tests (four native Windows skips); Ruff and MyPy pass.

The service source above is historical. Current source digest:
`bf0400161d841feb7825ef9aa94aca25e94a9ae23120ea73ec56da837bf9d159`.
The same reader reports zero violations, drift or failures. Calls and typing
multisets, all 298 UNKNOWN records, target and analyzer digests are unchanged.
Ceilings remain 1409/173/2/0/0; no ownership or permission changes. Completion
requires a new independently authored receipt bound to this source and the full
canonical Make gate. Actual final-head Sonar and CI remain separate requirements.
