# Step 115: evaluate the remaining UNKNOWNs

Source checkpoint: `9dc1961a`. Astra and Luna QA made independent first passes;
root reproduced the counts with published ArchKeel **1.0.0**. No source,
contract, descriptor, oracle or baseline changes. Evaluated uncertainty is not PASS.

All **254 canonical UNKNOWN records** are assigned a disposition in
[the ID inventory](step-115-unknown-disposition.json): 234 type positions,
eight re-export routes, six aggregate receipts, four API surfaces and two
global observation limits. The published counter measures exactly
**234 − 46 external types + 8 routes + 4 API surfaces = 200**.
Boundary counts are DSL 70, IO 31, Domain 46 and Runtime 49; four API surfaces
are unscoped. Aggregate receipts add no positions beyond their details;
the two global disclaimers add none.

| Position reason | Count | Disposition |
|---|---:|---|
| Inherited surface | 134 | 65 incomplete inherited inventories; 69 property-binding limits. Keep owner signatures; no forwarding copies. |
| External type | 46 | 39 stdlib types; seven external/validated aliases. Preserve actual types and validation. |
| Other | 15 | 14 TypeVar signatures; one callable alias with unresolved dictionary payload debt. |
| Generic | 11 | Preserve callbacks, factories and narrowing. |
| Ambiguous facade | 8 | Preserve overload return/nullability correlations. |
| Dotted name | 8 | Six RNG and two XML-element positions already use real types. |
| Missing annotation | 7 | Genuine source obligations; decisions below. |
| Forward reference | 5 | Existing Statement and SourceDistribution annotations. |

Astra approves **no source slice** from these seven obligations:

- `Statement.get_parent_full_name`: adding the return annotation exposes its
  Optional error. Preserve the native `None.split` failure; no cast or guard.
- Mongo/RDBMS config getters: preserve native dictionaries, Mongo's five keys
  and arbitrary nested RDBMS extras. Closed models misstate compatibility;
  honest broad maps leave the deferred boundary issue.
- `BaseLiteralGenerator.generate`: preserve the heterogeneous/custom extension
  contract. A union of today's subclasses is not its full contract.
- Two Memstore getters: preserve stored-row identity, mutation and open payloads.
  The existing read protocol does not prove every public `consume` payload.
- `Memstore.removeNotExistingIds.client`: preserve structural fake/custom
  clients and the direct call. Concrete-client restriction or the existing
  restrictive IO helper would change compatibility.

These are not blanket exemptions. Inherited surfaces may conceal real type
debt; property/callable signatures still carry dictionaries. The 69-property
group is an impact set for a separate getter/setter reproduction, not 69 proven
checker defects. Three class-surface flags concern decorated properties,
not observed top-level class control flow. Context/call limits remain open.
Parent-owned Interfaces initializer expression and Target physical-module
navigation remain separate unresolved gaps; no fake owner or hidden module.

LOCAL VERIFIED: all 254 IDs partitioned once, no additions/omissions; published
decoder/ratchet reproduces 200 and each boundary count. Caller/body traces for
all seven source obligations reviewed. Local and both CI artifacts have the
same source digest and identical 89 violation, 254 UNKNOWN and 491 module IDs.
The local packet retains its precommit `6433321f`/dirty metadata; it is not relabelled.
Scratch audit and independent receipts: `/tmp/ce-resume-20261008/unknown-audit/`.

CI-ONLY VERIFICATION: [push](https://github.com/rapiddweller/datamimic/actions/runs/37739313228)
and [PR](https://github.com/rapiddweller/datamimic/actions/runs/37739318404)
complete: each 24 successful, two failed, two skipped jobs. Product tests,
build, Ruff, MyPy and determinism matrix pass; E2E/release skipped. Definition
tests pass (8 + 4). Architecture validation fails at **89 violations / 200
UNKNOWN positions / two cycle edges**, with 58 findings beyond the baseline and none
resolved. Observation/coverage PASS; report generated and uploaded. Push scans
exactly `9dc1961a`; PR scans merge `09a49b97`, with identical source digest.
Full target, frozen DSL and Target-navigation acceptance remain open.
