# Amendment 172: explain the existing Interfaces–Domains dependency

2026-10-09. Base: `a52c70caf06d72a996fdd6a417a9597e7d54bde2`.

Only COMP-INTERFACES.requires[domains].rationale changes:

> CLI version and system-information commands read library version metadata through the Domains API.

`datamimic_ce/interfaces/cli/runtime.py:35–42` calls `domains.api.get_datamimic_lib_version`;
`datamimic_ce/domains/domain_core/runtime/determinism.py:16–21` reads installed library metadata.
Python adapters delegate generation through Runtime; Domains retains generation ownership.
This corrects stale explanatory prose, not the already declared dependency direction.

Astra and independent QA reviewed six Interfaces components and 14 files. Keep their
existing responsibilities, public surfaces, grants, selectors, rules and agent labels.
Source, tests, baseline and oracle remain unchanged. ArchKeel 1.0.0 evaluates
external routes through outer COMP-INTERFACES.requires; child requires governs
sibling routes inside Interfaces. No duplicate child grant is needed. External
callers/discovery and broader transport behavior remain UNKNOWN.

LOCAL VERIFIED: Ruff/MyPy (488 files) and 12 definition cases pass. Fresh report
exits 0 with observation/coverage PASS, declared FAIL: 88 violations, 200 measured
UNKNOWN positions and 254 canonical unknowns. Complete finding records and source
digest are unchanged. Against `a52c70ca` exits 2: no new widening, amendment status
null, baseline-new 57/resolved 0, 60 failures and 19 interface.usage_unknown diagnostics.
Initial cache-access failures occurred before analysis; successful v2 checks are separate.
Source/tests/config/baseline bytes match the base; Step148 native proof stays bound to a52c.
CI-ONLY VERIFICATION: pending for the new commit. The root gap, historical unbound
changes (#415) and full semantic/human acceptance of all 150 agent components remain open.
Bounded native/terminal CI evidence stays in the [protocol](protocol.md); no full DSL/EE/worker claim.
