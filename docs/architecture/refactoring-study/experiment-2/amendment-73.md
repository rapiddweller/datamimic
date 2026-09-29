# Amendment 73: declare existing demographic record types

Date: 2026-09-29. Decision: Astra.

`DemographicProfile` already exposes `DemographicAgeBand` and
`DemographicConditionRate` through the published loader and sampler. Their
owning nested contract declares the profile module, but the root Domains
boundary omitted these two record types. Declare both at `COMP-DOMAINS`.

No source export, runtime behavior, or broad map allowance changes. The
typed-map findings remain visible; their policy needs a separate decision.
