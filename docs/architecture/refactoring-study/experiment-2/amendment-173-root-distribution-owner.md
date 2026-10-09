# Amendment 173 — exact root distribution owner

2026-10-09. Base `c769121b079990a70ca777ea311cb93856587ec7`.

`COMP-DISTRIBUTION` owns only exact module `datamimic_ce`, with empty packages,
public and requires lists. The inert regular initializer anchors installed-distribution
origin; the existing wheel owner checks its `__file__` and installed module/spec paths.
The source review already records this distribution responsibility.

This supersedes only [Amendment 171](amendment-171-engine-namespace.md)'s unresolved-root
ownership clause. Preserve its namespace decision and compatibility limits, and
[Amendment 68](amendment-68.md)'s import purity. No descendant ownership, catch-all,
physical package, product/configuration change, API or dependency grant is added.
The root grows to 11 logical owners, 151 recursively; 25 contract levels and eight physical
root children remain. All 151 responsibility decisions remain agent-authored;
whole-target semantic and human acceptance are incomplete.

LOCAL VERIFIED: isolated missing-owner and package-only-guard REDs, then Main
`make architecture-definition-check` 13 PASS, Ruff PASS and MyPy PASS over 488 CE files.
Fresh report has complete observation/coverage but remains FAIL88 / 200 measured UNKNOWN /
254 canonical UNKNOWN; all decoded findings and CE source bytes equal c769.
Recorded projection closes the sole root gap; all descendant owners remain unchanged.
The unchanged global dynamic-call UNKNOWN now maps to the root owner; it does not
establish dynamic behavior in the inert initializer.
Baseline and unamended against-c769 validation both exit 2, with 57 new / zero resolved
baseline findings. Against adds one `distribution` component-presence widening;
amendment status is null. This reviewed addition is not a machine-bound amendment:
binding remains OPEN/#415. No baseline/oracle relaxation.
CI-ONLY VERIFICATION: no new-head claim. Historical Step147 wheel proof retains its
checkpoint bounds; fresh wheel, external discovery, other Python, EE and full DSL/worker
compatibility are not established by this declaration-only change.
