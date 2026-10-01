# IO owns export completion

Spec: `docs/architecture/inner/target.md` and `protocol.md`.
Decision: Astra, 2026-10-01; execution is covered by Alex's delegated architecture/refactoring approval.

## Constraints

- Preserve every existing descriptor, output byte, target order, worker ID and error path.
- Finalize all selected outputs before publishing any. Runtime retains statement traversal.
- Keep conditional-child publication's existing xfail unchanged.
- No wrappers, framework, new dependency, compatibility alias or allowance/budget increase.
- Preserve unrelated dirty changes. Only the coordinator commits/pushes this slice.

### Task 1: Extract IO-owned completion and cleanup

Implementer owns only:
`engine/io/exporters/{registry,lifecycle}.py`, `engine/io/api.py`,
`engine/runtime/tasks/generate/task.py` (under `datamimic_ce/`).

Move `_buffered_exporters`, `finalize_exporter_chunks`, and
`publish_exported_artifacts` from registry into `lifecycle.py` unchanged.
Extract the existing Runtime cleanup loop into
`cleanup_exporter_chunks(descriptor_dir: Path, task_id: str) -> None`.
Expose all three operations through IO API; call cleanup in the same finally
position, before Ray shutdown. Registry must not import lifecycle/session;
lifecycle must not import Runtime or DSL statements. Preserve existing dirty
smoke/SQL hunks.

Independent QA owns tests only. Reuse `test_generate_export_lifecycle.py`;
add narrow direct IO cleanup proof. Record RED before implementation starts.
Prove unrelated task chunks survive, publication/finalization failures clean
up without changing the exception, mixed formats and direct nested children
keep the global phase order, and cold SP/MP output stays valid. No altered
existing oracle, skips, xfails or descriptor files.

Coordinator owns contracts, module responsibilities, physical target map and
dated amendment. Declare lifecycle public operations and dependencies; retain
all measurement rules. Compare affected file descriptors before/after under
identical starting state. Run unit suites, full-package lint/typecheck,
recursive definition and cycle checks, then generate official 0.8.3 report.
Reviewer checks specification and code quality independently of implementer.

## Shared surfaces

| Producers / consumers | Surface | Order |
|---|---|---|
| QA / implementer | cleanup public signature | QA RED before production edits |
| implementer / coordinator | lifecycle module and public functions | disjoint files; integrate before gate |
| reviewer / coordinator | coherent diff + test evidence | review before commit |

Full corpus parity and zero material UNKNOWN remain final goal gates; this
bounded ownership change does not claim either is complete.
