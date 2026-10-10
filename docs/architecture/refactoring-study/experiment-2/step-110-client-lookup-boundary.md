# Step 110: type the existing client lookup

Base: `bde2a328`. Astra assigns `ClientLookup` to IO clients and declares its
exact parent boundary in [Amendment 161](amendment-161-client-lookup-boundary.md).
The two source files add the Protocol and replace the whole-map annotation.
The routing body and all Runtime source remain unchanged; mappings still work.
Independent Luna implementation and QA; Astra accepts the final architecture.

The rejected callable supplier reduced violations but added two UNKNOWNs.
Its patch, minimal checker reproducer and evidence remain in
`/tmp/ce-resume-20261008`; the prepared checker issue awaits publication approval.
No checker code, baseline, allowance, descriptor or oracle changes.

LOCAL VERIFIED: **2,290 units passed, 11 skipped, one existing xfail**; two
existing Pydantic serializer warnings. Six live Mongo routing tests pass on
both pristine baseline and final code, serially. Twenty-five ownership/QA
checks, source/changed-test Ruff, full MyPy (491 files, including a fresh
cache), recursive-definition checks and pinned executable-cycle Pylint pass.
The ownership-test file already fails whole-file formatting; the new block
is formatted and unrelated formatting stays untouched.

Frozen recorder: 931 XML inputs inventoried, 13 selected. Ten captures and one
expected error compare equivalent; all four projections are identical. The
strict comparison retains the same two incomplete captures and exits 1.
This does not establish full descriptor parity or report navigation acceptance.

Published ArchKeel **1.0.0** observes 491/491 files, AST coverage 100%.
Violations **91 -> 90**; UNKNOWN positions **202**, cycle edges **two** and
unresolved calls **1,231** stay unchanged. Only `VIO-05a115dec2c7a29f` disappears;
no new violation or UNKNOWN record appears. The strict architecture gate
remains **FAIL**. SQL injection compatibility and its cast debt remain unchanged.

CI-ONLY VERIFICATION: no passing remote result claimed for this slice.
PR #274 remains Draft; structure, full behavior, report exploration and final
delivery acceptance remain open. No merge or Pages work performed.
