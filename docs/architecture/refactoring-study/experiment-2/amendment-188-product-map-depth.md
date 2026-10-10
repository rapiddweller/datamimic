# Amendment 188 — exact product-map depths

Step 174. Astra approved the existing unwrapped
`Mapping[str, list[dict[str, object]]]` product envelope at the two IO facade
`products` positions. Keep the 26 previous `IO-API-TYPES` selectors unchanged.
For each position, add an exact `mapping_depth: 2` selector for the inner
string-keyed row map and an exact `mapping_depth: 2, container_depth: 3`
selector for its native value. This accepts opacity at the value; it does not
prove serialization or type closure. Fixed controls stay typed.

The IO capture and Memstore consumers retain product/row order, native value
identity, target selection, and existing partial-write and error behavior. This
is a contract-only correction: no production source, baseline, budget, oracle,
ownership, or dependency change. DTO wrappers, coercion, GroupMask,
GenerateFileSource, SQL155, and EE remain outside this decision.

Published ArchKeel 1.1.1 proved the unwrapped chain before the CE contract
edit: outer, inner and native grants remove only their respective findings.
Changed outer/inner keys, list, value, qualified name, position and annotation
retain findings; wrong field path and mismatched depth pair are rejected by the
parser. The sibling and fixed-control findings remain. The separate
`Annotated`-wrapper false grant in ArchKeel #434 remains open; these checks do
not establish wrapper-negative correctness.

The full report moves from 17 to 13 findings by removing only
`VIO-0cb2e65d6c7b8020`, `VIO-50a941c5eac71c66`,
`VIO-8dcaf88aaa1dfabf`, and `VIO-eeff7c478475b871`. All surviving records,
all 254 canonical UNKNOWN records, and the source digest match exactly.
`declared_rules` remains FAIL. The [receipt](step-174-product-map-depth-receipt.json)
pins reports and local gates.

LOCAL VERIFIED: selector guard RED then GREEN; 81 focused checks pass with 11
existing skips; 13 definition checks, Ruff and full MyPy (488 files) pass.
Native validation exits 2 with 19 usage-UNKNOWN diagnostics, 9 baseline-new
groups and zero baseline-resolved groups. This is not target acceptance.
CI-ONLY VERIFICATION: pending. Full DSL/EE acceptance remains open.
