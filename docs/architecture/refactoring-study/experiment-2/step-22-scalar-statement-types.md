# Step 22: type scalar statement getters

`KeyStatement` and `ElementStatement` now return the types already declared by
`KeyModel`: six `str | None` fields and `unique: bool | None` each. No parsing,
generation, or descriptor changed. EE has the same statement roles but richer
model types; this step does not claim type parity.

Independent Luna implementation and QA passes preceded root review. The QA
agent's new weighted-key tests duplicated existing integration cases, so they
were removed. Existing weighted, XML-element, authoring rejection, and seeded
descriptor tests cover the affected paths.

The candidate ArchKeel report changed from 251 to 237 UNKNOWN positions: the
14 missing-return-annotation records disappeared, with no new UNKNOWN records.
Violations remain 124 and cycle edges remain 2. The 13 `interface.unused`
diagnostics tracked by ArchKeel #204 still block validation.

LOCAL VERIFIED: 72 focused descriptor tests; unit suite 1419 passed,
11 skipped, 1 xfailed; project-venv Ruff and MyPy (488 files); report
observation complete, coverage PASS. Full descriptor inventory and CI were
not run for this step.

CI-ONLY VERIFICATION: not run.
