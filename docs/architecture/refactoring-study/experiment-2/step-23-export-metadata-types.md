# Step 23: type export-routing metadata

`ExportMetadata` declares the three existing routing keys at the IO boundary.
Runtime still builds the same dictionary; IO still emits a two-item tuple when
it is empty and a three-item tuple otherwise. No descriptor or routing policy
changed. The `contracts.py` responsibility sentence now names export routing.

Independent Luna implementation and QA passes preceded root review. Root kept
the existing DSL constants as the single source of key names and removed
redundant assertions. The candidate ArchKeel report drops from 124 to 121
violations: exactly three `dict[str, str]` metadata messages disappear, with
no new violation messages. UNKNOWN positions remain 237; declared rules still
fail, including the 13 `interface.unused` findings tracked by ArchKeel #204.

LOCAL VERIFIED: 19 focused tests; 107 exporter/source matrix and exporter
tests; 1421 unit tests passed (11 skipped, 1 xfailed); five architecture
definition tests; project-venv Ruff and full-package MyPy (488 files); pinned
Pylint cyclic-import gate; candidate ArchKeel observation and coverage PASS.
The full frozen descriptor inventory and service-backed tests remain open.

CI-ONLY VERIFICATION: not run.
