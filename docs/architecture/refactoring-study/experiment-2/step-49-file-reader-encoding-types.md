# Step 49: type file-reader encoding

Twelve `FileUtil` reader methods now declare their existing `encoding`
parameter as `str`. Their defaults and behavior did not change. The
fixed-width reader was already typed.

With the same local ArchKeel candidate, the CE report moves from 94
violations / 190 counted UNKNOWN positions to 94 / 178. This resolves twelve
missing-annotation UNKNOWNs; it does not claim any boundary violation is fixed.

LOCAL VERIFIED: independent QA reviewed the diff and ran 62 relevant reader,
properties, authoring dry-run, fixed-width, and DbUnit tests. Implementation
also ran Ruff and mypy over all 491 CE modules. The recursive target
definition tests passed 5/5. `make architecture-definition-check` could not
start because this sandbox blocks uv's user cache and tool directory; the
same test files passed from the project venv. The report artifact is
`test-artifacts/architecture/ce-current-step52-typed-encoding/architecture.report.html`.

CI-ONLY VERIFICATION: not run. The full descriptor oracle was not rerun for
this annotation-only change.
