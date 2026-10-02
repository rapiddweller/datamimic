# Step 60: type CSV reader results

Four CSV readers now declare the string rows and header indexes they return.
No parsing or cache behavior changed. Tests pin quoted delimiters, BOMs, ragged
rows, malformed cached rows, and the existing empty-file behavior.

LOCAL VERIFIED: 19 focused tests passed, including the empty-CSV XML descriptor.
Full-package MyPy (491 files), Ruff, recursive target-definition tests (5), and
`git diff --check` passed. Independent Luna QA checked callers and result shapes.
CI-ONLY VERIFICATION: not run for this step. The external-service descriptor
matrix and full descriptor equivalence gate remain open.

Separate finding: the CSV cache is keyed by path, not separator or encoding.
This is a behavior risk, not a result of the type change; fix and verify it as
its own slice.
