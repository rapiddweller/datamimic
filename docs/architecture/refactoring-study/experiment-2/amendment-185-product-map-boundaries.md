# Amendment 185 — outer product maps

2026-10-10. Decision: Astra, delegated architect. Base `086098392d70f20f8d42de03b16ee8d6de6a40ee`.

Runtime merges worker results and determines capture/storage timing. IO consumes
the outer mapping from dynamic product names to existing row lists. Permit only
that outer `Mapping[str, list[dict[str, object]]]` at `IO-API-TYPES`, position
`products`, empty field path, for `datamimic_ce.engine.io.api.capture_test_results`
and `.consume_memstore_target`. Add two selectors without container depth;
retain the existing 24 selectors exactly. Inner row maps and native values remain
open findings. This lifts Amendment 181's product-map hold only at the outer map.

Keep Amendment 168's Memstore owner and Amendment 99's capture semantics.
Read-only product mappings work; capture preserves product order and native
row/value identity, normalizes names and replaces stored outer lists. Earlier
writes survive a later failure. Memstore writes only the first known target,
uses targetEntity/type/name priority, registers missing products as empty and
does not read the map without a target. Native errors and lookup/type-check
order remain unchanged. Worker/Context bare types and external typed callers
are not proven closed; the declared dictionary-row inputs are not broadened.

No production, ownership, dependency, baseline, budget or oracle change.
Properties, Cache, GroupMask, SQL155 and EE retain their separate scope.
The published 1.1.0 report confirms 24 → 22 findings; all 22 remaining records
and 254 canonical / 200 measured UNKNOWNs are unchanged. Two new allowance
facts add no opacity; 11 existing facts gain only this amendment's provenance.

LOCAL VERIFIED: 27 dispatch checks pass before the contract edit; the exact
26-selector guard fails, then passes with identical test bytes. The selected
cohort passes 91 tests with 11 existing Ray-rework skips; all nine selected
SP/MP capture, zero-count and nested Memstore lifecycle cases pass. This does
not establish live worker transport. Package/changed-test Ruff and full MyPy
(488 files) pass. All 13 Makefile definition checks pass in the project venv
after the uvx launcher cannot access its sandboxed cache. An isolated published
1.1.0 source fixture removes only the two outer findings, retains four inner
findings and rejects changed outer keys/containers while preserving seven
fixed-control/sibling findings. No accepted opacity is added. Production bytes
and pre-existing protected files remain unchanged.
Independent QA confirms native behavior, negative selector/source controls and
the exact full-report comparison. Native amendment validation retains the
widening but exits 2 with the same 19 usage-UNKNOWN diagnostics and 14 baseline-
new groups; no machine artifact is emitted.
CI-ONLY VERIFICATION: new-head checks pending; full DSL/EE remains open.
Evidence: `/tmp/ce-resume-20261010/next-slice-172/`.
