# Step 132 — truthful transaction-profile metadata

Date: 2026-10-08. Baseline: `1904b4a06f16e5d57feacbf3f6a94436a40a5a6e`.
Decision: [Amendment 165](amendment-165-transaction-profile-catalog.md).

PersonService and PatientService now declare `(str, Mapping)` for their existing
transaction-profile values. Their two model-documentation rows match the getter
annotations. No runtime function, renderer, architecture permission or EE file changed.

LOCAL VERIFIED:

- Baseline regression: 4 intended assertion failures and 6 passes; candidate: 10 passes.
  Actual non-dict mappings retain identity, backing mutation and native JSON rejection.
- All 23 named reference pages and schemas compared through canonical Authoring;
  CLI output equals content plus one newline. Exactly two field declarations and
  two reference lines changed. Other 21 pages, index and result metadata are unchanged.
- Four frozen projections remain byte-identical; they omit named detail pages.
- Relevant five test owners: 114 passes. Full-package Ruff and MyPy: pass, 491 files.
  Changed-file formatting: pass. Architecture definition: 8 passes; cycle check: pass.
- Published ArchKeel 1.0.0 report: 491/491 parsed, observation PASS, declared rules FAIL.
  Still 89 violations and 200 measured UNKNOWN positions; no acceptance claim.
- One-shot baseline/candidate captures retain raw output, origins and unchanged
  975 Python / 1,024 packaged-data snapshots. Independent implementation and QA readback.

CI-ONLY VERIFICATION: no candidate CI result established at this local checkpoint.

Evidence: `/tmp/ce-resume-20261008/next-slice-132/`, including raw captures, JUnit,
root validations, independent QA and the full architecture packet. Packet SHA-256:
`42715c49ac8d099ffb054f0bf5402664eab25a11b582c8d2ed8d4be6756c009a`.

UNKNOWN: external consumers of the old dict identity/reference bytes, complete
CLI-child module origins, full DSL parity and full CE/EE/report acceptance.
This metadata correction does not close those requirements or replace their evidence.
