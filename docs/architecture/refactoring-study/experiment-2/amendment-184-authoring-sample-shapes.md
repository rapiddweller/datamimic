# Amendment 184 — complete Authoring sample annotations

2026-10-10. Decision: Astra, delegated architect. Base `ec8d16bfffe007c1846fd19356d121df0ef583f1`.

Authoring owns the bounded JSON sample projection of native Runtime captures.
`ProductResult.sample` is `list[dict[str, JsonValue]]`; both `RunResult` and
`ScaffoldResult` reuse it. Scalar rows become value maps; nested/native values
follow the existing clipping and JSON validation. Counts and acceptance retain
the complete bounded capture independently of the sample limit.

Correct only the two existing `AUTHORING-API-TYPES` annotations for
`datamimic_ce.authoring.api.run` and `.scaffold`, position `return`, field path
`products.sample`: `dict[str, JsonValue]` becomes `list[dict[str, JsonValue]]`.
Amendment 11 already chose these fields; this corrects its incomplete type
spelling without rewriting that historical record. Append this provenance;
all other selectors and rule fields remain unchanged. No depth or native
object allowance is introduced.

Production, schemas, transports, baseline, budgets and oracle are unchanged.
GroupMask, Properties, Cache, SQL155 and EE remain outside this decision.
Fresh ArchKeel 1.1.0 report: FAIL24 (26 → 24). All 24 remaining findings,
254 canonical UNKNOWNs and existing allowance facts are identical; measured
UNKNOWNs remain 200. Two new precise allowance facts add no accepted opacity.
Source facts and topology are unchanged. This is not full DSL/EE or target acceptance.

LOCAL VERIFIED: the exact four-selector guard fails before the correction;
108 Authoring/public-contract/dry-run/scaffold/CLI/MCP tests then pass with
identical test bytes. Package/changed-test Ruff and full MyPy (488 files) pass.
The Makefile's 13 definition checks pass in the project venv after its uvx
launcher cannot access the sandboxed cache. No production or schema changed.
Independent QA passes eight focused tests, eight wrong-selector pairs and two
single-selector removals; sibling and fixed-control findings stay unchanged.
Native amendment validation retains the Authoring widening but exits 2 with
the same 19 usage-UNKNOWNs and 14 baseline-new groups; no machine amendment is emitted.
CI-ONLY VERIFICATION: new-head checks pending.
