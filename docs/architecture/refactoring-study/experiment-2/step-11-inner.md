# Step 11: CE inner architecture

Control: Draft PR #274 at `e35d599c`. Implementation and QA worked in separate Luna
checkouts; the orchestrator reviewed and integrated their commits in an isolated clone.
No XML descriptor was edited.

The physical CE core now groups Authoring, DSL, IO, Runtime, Domains, and shared errors
under their approved owners. The five inner ArchKeel contracts are active. A physical
test checks required paths, rejects `domains.common`, and prevents Runtime tasks from
importing concrete IO clients through the facade. `errors/context/` is deferred by
Amendment 18: CE has no consuming error API, and the tested prototypes either changed
descriptor error behavior or violated the no-reflection rule.

ArchKeel 0.7.0 parses 488/488 files: 0 rule violations, 0 UNKNOWN positions, and no
new baseline finding. `--against e35d599c` passes with the recorded amendment. The
`cycle_edges` ratchet narrowed 171 → 11; the remaining observations are type-only
imports and package rollups, not an assertion of runtime cycles. The pinned Pylint
cyclic-import check passes separately. ArchKeel 0.7.0's inner contracts do not yet
enforce complete module assignment or all internal interface/cycle semantics, so
the physical test and Pylint are necessary independent checks.

The independent error QA found that a broad `ValueError` catch mislabeled unsupported
versions and missing locale data as E002. The loader now marks only an unsupported
locale dataset with a typed exception. Existing malformed-locale schema errors stay
unchanged; a valid-shaped unsupported locale uses EE's E002 code. Public error
pickling and the legacy `DomainError` string behavior have focused tests.

Local verification:

- 3,856 non-service tests passed; 28 skipped. The unit-only coverage gate passed:
  1,201 passed, 11 skipped, 68.01% line coverage. The 90% unit-coverage goal is not
  reached by this structural refactor.
- The 930-XML inventory is unchanged; no XML file was edited. Of these, 454
  descriptors were captured (88 seeded, 366 unseeded), 62 produced expected errors,
  16 were not runnable descriptors, 76 were unrunnable, and 322 remain unverified
  by the generic oracle (including 273 service descriptors). All 88 seeded captures
  match the frozen control, and a second candidate run matches all 88 again.
- The raw comparator reports five differences, not a clean pass: the MemStore test
  gained an assertion; two unseeded captures sampled different valid rows/condition
  branches; the Atlantis error embeds the relocated resource path; and the full
  capability output reports a different package `schema_version` (4.1.0 versus
  4.3.1.dev89+dirty). Removing only that version field gives identical capability
  content; the other three projections have identical hashes. Twelve repeat runs
  on each revision reproduce the two unseeded variations. These are classified
  differences, not byte-identical output or a silent comparator pass.
- Four selected Postgres/Mongo DSL tests passed on each revision against separate,
  fresh, no-volume OrbStack containers. The checked-in development settings point
  at shared databases and were not used. This does not verify all 273 service
  descriptors.
- Ruff, full-package MyPy, the physical layout test, pinned Pylint cycles,
  ArchKeel 0.7.0, and the offline sdist/wheel build passed. The wheel includes the
  moved Authoring, Runtime, DSL, IO, Domain, and Errors packages.

Remote CI is pending until this local result is committed and pushed to Draft PR #274.
