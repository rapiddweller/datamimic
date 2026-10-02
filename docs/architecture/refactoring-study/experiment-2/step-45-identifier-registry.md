# Step 45: Domain-owned identifier registry

Moved identifier collision handling from `BaseEntity` into a Domain-owned
`IdentifierRegistry`. `SetupContext` creates and copies it; services and nested
entities share it within a run. [Amendment 67](amendment-67.md) declares the
actual cross-component type. No descriptor source changed.

With local ArchKeel `0.8.1.dev20+g0c1252490`, violations moved 106 → 97:
seven inherited Domain setter findings and two Runtime context positions are
gone. `baseline_new` moved 84 → 76; material UNKNOWN positions stayed 189.
All 490 Python files parse with 100% AST coverage. The architecture gate is
still red; this step does not claim the target is reached.

The seeded Domain-ID tests assert exact values and replay; the runtime
descriptor test asserts stable IDs across pages and worker policies. The
deepcopy test checks that copied runs retain prior claims without sharing later
claims with the original. Six selected descriptor captures match the earlier
CE capture: both seeded result/output digests match; four unseeded outcomes,
counts, value shapes, and output-file lists match. Authoring compiler and
reference projections match; capability hash still carries the known
version-sensitive drift from Amendment 60.

LOCAL VERIFIED: 1,472 unit tests passed (11 skipped, one xfailed); 60 focused
Domain/runtime tests; 15 architecture tests; Ruff, full-package MyPy, Pylint
import-cycle check, five target-definition tests, `git diff --check`, local
ArchKeel report/validation, and the selected descriptor/projection comparison.
Independent QA ran 111 related tests; Astra found no actionable boundary defect.
CI-ONLY VERIFICATION: not run. Full descriptor-corpus and service-backed parity
are still open.
