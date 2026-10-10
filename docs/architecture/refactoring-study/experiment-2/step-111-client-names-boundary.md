# Step 111: type exporter client names

Base: `12d5e3a5`. [Amendment 162](amendment-162-client-names-boundary.md)
declares the exact IO-owned `ClientNames` Protocol. `ExporterContext.clients`
requires membership and name enumeration; retrieval remains a separate method.
Two source files change. Existing executable bodies and all Runtime source
remain unchanged; dictionaries and read-only mappings structurally conform.
Independent Luna implementation and QA review the same bounded brief;
Astra accepts the final bounded architecture slice.

LOCAL VERIFIED: **2,291 units passed, 11 skipped, one existing xfail**;
two existing Pydantic serializer warnings. Thirty-seven file-export integration
tests and twenty ownership checks pass. Source/changed-test Ruff, full MyPy
(491 files), pinned executable-cycle Pylint, eight recursive-definition checks
and four inner-target checks pass. Existing whole-file ownership-test formatting
debt remains untouched.

Published ArchKeel **1.0.0** observes 491/491 files, AST coverage 100%.
Violations **90 -> 89**; measured UNKNOWN positions **202**, cycle edges **two**
and unresolved calls **1,231** remain unchanged. Only `VIO-8ce9a22d25bb725e`
disappears; no new violation or UNKNOWN record appears. Strict architecture
validation remains **FAIL**, with 58 new baseline findings. No checker, baseline,
allowance, descriptor or oracle changes; SQL cast compatibility debt remains.

Frozen recorder: 931 XML inputs inventoried, 13 selected; ten captures and one
expected error compare equivalent. All four before/after projections match.
The strict comparator exits 1 for the same two incomplete captures. Historical
capability projection drift remains open. Neither bounded evidence nor source
equality establishes full DSL parity or all-depth report acceptance.

CI-ONLY VERIFICATION: no passing remote result claimed for this slice.
PR #274 remains Draft. The overall target and report acceptance remain open.
Evidence: `/tmp/ce-resume-20261008/names/`.
