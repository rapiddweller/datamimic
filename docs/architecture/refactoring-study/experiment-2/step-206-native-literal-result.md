# Step 206 — native literal-generator result

`BaseLiteralGenerator.generate -> object` declares the existing extension
result. Built-in subclasses keep their precise returns; Runtime retains value
handling. Only this abstract base return receives an exact allowance through
[Amendment 206](amendment-206-native-literal-result.md).
This is accepted opacity, not full native type closure.

Independent Astra review approves the five committed source/contract/test files.
Source commit `7f0f6cd8b2f9104f152d3a2d42d8c89acffbda5f` has the same blobs as
reviewed clone commit `1d5738c15630e4b99a7c4a08ce414391f96bb580`.
The sole production edit is the return annotation. Abstract body, RNG, cache,
callers, specialized returns and all 24 recursive contracts stay unchanged.

Published ArchKeel 1.1.1 measures three phases:

| Phase | Violations | Canonical UNKNOWNs | Scalar positions |
|---|---:|---:|---:|
| Before | 12 | 254 | 200 |
| Annotation only | 13 | 253 | 199 |
| Exact allowance | 12 | 253 | 199 |

The annotation removes only one missing-annotation UNKNOWN and first produces
an opaque-boundary finding. The exact allowance replaces only that new finding
with its accepted-opacity fact. The original 12 findings and other 252 UNKNOWN
records remain exact; the domain aggregate reflects its one decided position.
Prior allowance facts gain only Amendment 206 provenance.

Fresh primary measurement confirms these canonical records and 17 recorded
sections match the reviewed candidate, with 488/488 files and 100% AST coverage.
Its actual source HEAD and `dirty=true` provenance are retained; protected
untracked `evidence/` and `.playwright-mcp/` remain untouched.
[Receipt](step-206-native-literal-result-receipt.json) pins source and raw evidence.

LOCAL VERIFIED: reviewed candidate has 62 focused passes, 2410 unit passes,
11 skips and one expected failure; Ruff, full MyPy (488 files) and 13 definition
checks pass. Tests retain sentinel/None/map and exception identity, one invocation,
ABC/RNG/cache behavior. Published evaluator accepts the actual selector and
rejects nine negative controls; counterfactual IR cases are disclosed in raw proof.
Primary integration rechecks committed hashes and fresh report, without repeating
the unchanged broad suites.

Native amendment writing still refuses 19 existing usage UNKNOWNs. The explicit
agent semantic amendment is machine-bound using the published recursive verifier;
four tampered digest controls fail. Ordinary validation reports amendment valid
and no unamended widening, but exits 2 with declared rules FAIL. Neither native
writer success nor complete validation acceptance is claimed.

CI-ONLY VERIFICATION: pending for the integrated source/evidence head.
The DSL ledger remains 174/931 reviewed and 757 UNKNOWN. No native `while`
execution or ledger admission follows from collect-only preparation.

Saved Atlas payloads omit applied-allowance presentation while canonical and full
projection evidence retain it. Rendered UI behavior remains unverified; keep this
separate from CE runtime and contract acceptance.

Skipped integration/services/EE, full type closure and rendered UI acceptance.
The twelve violations, remaining UNKNOWNs and whole CE/EE target remain open.
