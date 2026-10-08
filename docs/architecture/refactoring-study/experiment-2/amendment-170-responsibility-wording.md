# Amendment 170: clarify existing responsibilities

2026-10-09. Base: `4eaede0adf43be4ec879122635b95930bffb6a90`.

IO's blanket context-reading prohibition contradicted the already approved
[IO-owned ExporterContext boundary](../../inner/semantic-review/astra-target-decision.md).
The prohibition now names concrete Runtime contexts, DSL statements and access
beyond that existing protocol. Expression evaluation and task orchestration remain forbidden.

RUNTIME-API now names its existing lifecycle, context, generator-capability,
descriptor-property and environment surface. Implementations retain their current owners.

Only two responsibility sentences change. Source, public/requires entries, selectors,
rules, baseline, oracle and all `agent` decision labels are unchanged. Astra reviewed
this against the existing decisions and callers; it does not confirm all 150 components.

LOCAL VERIFIED: Make lint/typecheck (489 files), 12 definition cases, fresh 1.0.0 report
and against-base validation. Observation/coverage PASS; declared FAIL remains 88
violations/200 measured UNKNOWN positions (254 canonical unknowns). Complete violation
and unknown records and source digest are unchanged. Against-base exits 2, with two
prose-field widenings, 62 failures and 19 diagnostics; baseline-new 57/resolved 0.
Astra approved these exact clarifications as a RED checkpoint. Neither widening is
machine-bound; amendment status is null and [binding issue #415](https://github.com/rapiddweller/archkeel/issues/415)
remains open. No writer was used. CI-ONLY VERIFICATION: pending for the new commit.
Broader semantic responsibility, DSL/EE compatibility and architecture acceptance remain open.
