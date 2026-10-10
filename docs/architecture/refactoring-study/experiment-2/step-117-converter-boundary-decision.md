# Step 117 — converter boundary decision

Decision: retain the 19 converter violations. No compatible source-only repair
is approved. This is a real mismatch with the current target, not a demonstrated
checker defect. Overall acceptance remains **FAIL**.

## Finding index

At `c65d0090`, the unchanged source digest is
`d5fdc6789839b6dabade4917eb545f6f9aa5bf0b82e71baca46f89c0be3625d6`.
[The ID index](step-117-boundary-families.json) partitions all 87 boundary
findings exactly once. Only the selected converter family received a complete
producer/caller/extension review; the other 68 remain an investigation index.

| Shared contract | Findings |
|---|---:|
| IO rows, source results and export payloads | 35 |
| Converter values and context — reviewed | 19 |
| Demographic keyed data and propagated configuration | 18 |
| Runtime requests, state and captures | 10 |
| DSL property maps and aliases | 2 |
| Authoring JSON samples | 2 |
| Finance permissive account input | 1 |

Families cross facade boundaries: Domain 35, IO 35, Runtime 13, DSL 2,
Authoring 2. Three Runtime findings belong to the demographic family.

## Compatibility evidence

Runtime constructs `list[Converter]` from built-ins and script-defined classes,
injects custom contexts unchanged, then applies the chain to scalar, list,
nested-key and whole-product values. Converters are public and available in the
script namespace; the shipped custom-component example subclasses this API.

The 19 positions comprise 12 specialized inputs, two base positions, three
CustomConverter positions and two structural-converter positions. Specialized
converters already return precise scalar types and validate unchecked inputs
with native errors. Narrowing their annotations conflicts with the base and
caller contracts; moving validation would change the dispatch/error boundary.
The structural converter returns arbitrary non-container objects by identity.
Custom contexts and extension results have no finite product schema.

No wrapper, closed union, concrete Runtime-context dependency, export removal,
cast, suppression or allowance is justified. Existing inner converter ownership
needs no physical move. EE's corresponding API also accepts arbitrary values;
its RNG dispatch is a separate behavior, not a CE typing repair.

## Verification

LOCAL VERIFIED: independent Astra and Luna first passes and their counterchecks
agree. Root reran 11 structural/construction/context tests and 23 scalar tests:
**34 passed**. No production, contract, descriptor, oracle or baseline changed.

CI-ONLY VERIFICATION: exact `c65d0090` runs
[37744034314](https://github.com/rapiddweller/datamimic/actions/runs/37744034314)
and [37744041716](https://github.com/rapiddweller/datamimic/actions/runs/37744041716)
each completed with 24 successful jobs, two architecture failures and two skips.
Product tests/build/Ruff/MyPy/determinism passed; E2E/release were skipped.
The first artifact scanned this exact commit using published ArchKeel 1.0.0;
its source digest and all 89 violation, 254 UNKNOWN and 491 module IDs match the
local packet. The gate retains 200 measured UNKNOWN positions, two measured
cycle edges and 58 new baseline findings. These checks do not establish full
DSL parity or all-depth report acceptance.

Next: supplemental captures for a reviewed local-only descriptor lane. Keep
the frozen captures and remaining acceptance failures intact.
