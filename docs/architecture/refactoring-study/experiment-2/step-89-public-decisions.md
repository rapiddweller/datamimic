# Step 89: explicit inner API decisions

2026-10-02. Base `0b0dc64b`; released ArchKeel 0.8.4. Astra's Amendment 88
assigns the existing Authoring initializer exactly to AUTHORING-API, makes
Registry's empty public interface explicit, and declares four existing request/
generate entries in each of Shared and Healthcare. No production move or export.

The first draft put five external aliases in internal interfaces. Validation
rejected ten unused entries. The external declaration attempt then exposed twelve
missing types; adding them still failed ten literal-export checks. Both attempts
were rejected, not committed. Astra split the internal ownership correction from
the unfinished external API review. Root external declarations and source remain
byte-identical to the base.

## Same-checker result

| Measurement | Before | After |
|---|---:|---:|
| Parsed CE modules | 492 | 492 |
| Violations | 106 | 106 |
| Counted UNKNOWN positions | 157 | 157 |
| Unresolved calls | 1269 | 1269 |
| Package cycle edges | 2 | 2 |

AUTHORING-INTERFACES and AUTHORING-REQUIRES-COMPLETE move from UNKNOWN to proven
PASS. Shared and Healthcare interface receipts remain UNKNOWN without complete
evaluator proof. The violation signature is unchanged:
`d68909863672306723ac41c795b6ffb55b154fb88e8147df6f743c48413690db`.

`validate --baseline --against 0b0dc64b` exits 1, not 2: no contract-invalid
diagnostics remain. Amendment 88 binds the exact contract digests. Global FAIL
persists: 69 fingerprints absent from the frozen baseline plus measurement drift.
The baseline is unchanged; no new debt was accepted.

Disposable negative probes catch a same-prefix sibling and private-helper import.
The sibling layout violation has evaluator proof; the helper's outer interface
violation lacks complete receipt proof. Neither establishes full inner-interface
coverage. Root's separate complete inheritance fixture reproduces an external
API false PASS, tracked in [ArchKeel #243](https://github.com/rapiddweller/archkeel/issues/243).
Simple aliases correctly check their own fields; complex CE closure is unfinished.

LOCAL VERIFIED: independent literal decision test and unchanged transport/domain
tests (20 passed); implementer service/transport/facade set (37 passed); standard
definition checks (7 passed), Pylint executable import-cycle check, Ruff and
full-package MyPy (492 source files). These test sets overlap; do not sum them.
Production, descriptors, oracle and baseline bytes are unchanged. Full DSL corpus
was not rerun for this contract-only step.

Astra's independent spec/quality review permits this scoped checkpoint. The diff
proves the initializer-only declaration change; an observed before/after owner
table was not retained, so complete ownership-delta proof is still missing.

CI-ONLY VERIFICATION: pending for this step. PR274 remains Draft. The 0b0dc64b
pipeline passed tests, services, replay, lint/types/build and Sonar; architecture
failed. The complete CE target, DSL acceptance and report usability remain open.
