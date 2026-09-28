# Step 18: Generate database reads belong to IO

Runtime still resolves statement values, interpolation, offsets, file and
memstore precedence, and target intent. IO now chooses MongoDB versus RDBMS
read operations, including the MongoDB empty-upsert case. The new operation
takes resolved values, not a runtime context or DSL statement. No XML
descriptor was edited.

Independent Luna implementation and QA passes preceded root review. Review
restored selector interpolation timing and removed client-family decisions
from Runtime. QA covered SQL and Mongo query/entity routes, pagination,
upsert, missing source attributes, unsupported clients, offset rejection,
and file/memstore precedence.

LOCAL VERIFIED: 41 focused source-routing tests and 1,393 unit tests passed
(11 skipped, one expected failure). Nine target-definition tests, Ruff,
full-package mypy (487 files), Pylint cyclic imports, and `git diff --check`
passed. The integration suite previously ran against these production changes:
552 passed, two skipped; its one sandbox-blocked local SSE socket test passed
when rerun with socket permission. The functional suite passed 133 tests.
Four selected old/current descriptors were recaptured under the corrected
oracle: three `CAPTURED` pairs were equivalent; the dynamic nested-count case
was `UNVERIFIED` in both trees. All 930 tracked XML hashes still match the
frozen descriptor inventory.

CI-ONLY VERIFICATION: not run. Full old/current descriptor capture,
service-backed cases, and final target acceptance remain open. An
`UNVERIFIED` dynamic case is not a parity claim. The local ArchKeel candidate
reports one new `IO-API-TYPES` finding for the returned dynamic database row
shape (`list[dict[str, object]]`); the target type rule is not yet met. Its
`validate` result is `UNKNOWN` (94 baseline-new findings and 13 inherited
public-interface diagnostics), not a green architecture gate.
