# Step 08C14: finish public crossings and explicit domain discovery

## Change

- Routed every interface-to-Authoring import through the new typed `authoring.api` and
  `authoring.contracts` surfaces.
- Routed shipped demo context imports through `runtime.api`, removing the final private component
  crossings.
- Replaced package scanning for built-in domain generators and entities with explicit ordered
  inventories.
- Removed 23 additional domain type escapes without introducing a broad catch-all value type.

The Authoring and domain lanes were implemented independently and integrated as one measured step.
The Authoring schema hook adds three third-party calls ArchKeel cannot resolve; the domain lane
removes seven unresolved calls, so the combined ratchet still improves from 1,403 to 1,399.

## Evidence

- ArchKeel violations: 272 -> 234; 31 baseline fingerprints resolved and 0 added.
- Private component crossings: 8 -> 0. Domain dynamic imports: 3 -> 0.
- NO-MAGIC findings: 258 -> 231. Domain NO-MAGIC findings: 145 -> 119.
- `calls_unresolved`: 1,403 -> 1,399; typed positions: 421 -> 390; component graph remains
  acyclic.
- Authoring focused gate: 11 passed. The live MCP scaffold input-schema hash remains
  `fa36a2e3d1da2f82cf1767a4649e6f2b3269eb5d7d12b82f5282d773221b6d51`.
- Domain gate: 1,149 unit tests passed (11 skipped), plus 22 relevant integration and functional
  tests. Fresh-process inventories match the prior 23 entities, 34 generators, and 92 aliases in
  the same order and with the same lazy import timing.
- Final integrated descriptor oracle against frozen Step 0: 930 compared, 0 differences, and 0
  optional-shape variances. All four Authoring projection hashes are unchanged.
- Ruff and diff check pass. Full-package mypy still reports only the two missing optional Ray
  imports.

## Compatibility note

The MCP/JSON contract is unchanged, including nested container identity and the generated schema.
Python callers that inspect a `ScaffoldRequest` directly now receive `AuthoringDocument` at
`request.spec` and `AuthoringExpectation` items at `request.acceptance_requirements`; their prior
dictionary or typed expectation is available at `.root`. ArchKeel 0.6.0 rejects both direct fields
as unowned boundary types even when they use Authoring-owned aliases.
