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

CI-ONLY VERIFICATION: not run. Service-backed descriptor cases and final
target acceptance remain open. An
`UNVERIFIED` dynamic case is not a parity claim. The local ArchKeel candidate
reports one new `IO-API-TYPES` finding for the returned dynamic database row
shape (`list[dict[str, object]]`); the target type rule is not yet met. Its
`validate` result is `UNKNOWN` (94 baseline-new findings and 13 inherited
public-interface diagnostics), not a green architecture gate.

## Same-oracle recapture of the frozen Step 0 tree

Commit `c7aad450` changed only the verification oracle so it can import the
pre-move Python layout. The frozen Step 0 code and current code were then
recaptured with that same oracle and unchanged XML. Of 930 descriptors on each
side, 344 were `CAPTURED`, 62 `EXPECTED-ERROR`, 16 `NOT-A-DESCRIPTOR`, 76
`UNRUNNABLE`, and 432 `UNVERIFIED`. The final comparator accepts 403 pairs:
325 captured results, 62 expected errors, and 16 non-descriptors. Another 508
pairs remain unproved. The final recapture has 19 `CAPTURED` pairs that fail
comparison: ten differ under unseeded random choices, source ordering, or
multi-process shard assignment; nine fail even against themselves because
all-null or zero-row output has insufficient shape evidence. Independent
repeated captures on both code trees support these classifications. They are
not blanket exclusions or a full parity pass.

Compiler and both reference projections match. The full capabilities output
does not: its development version and descriptions naming moved utility classes
changed. Amendment 60 accepts only the enumerated wording corrections and
package-version metadata difference. The comparator now checks that narrow
exception against the raw projections. The final current recapture preserves
all 930 status counts and passes that narrow projection comparison. Its raw
comparator still exits 1 for the 527 descriptor differences above. The
62 expected-error records have the same captured exception class and normalized
message; their owning tests remain the semantic check. No remote CI was run.

`verify_step0.py --capture-only` writes the raw projection drift and exits after
capture; only `compare_step0.py` evaluates the reviewed exception. Without that
flag, the historical raw-hash gate still exits 1.
