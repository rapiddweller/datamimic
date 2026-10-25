# Include budget and property targets review (PR #383, #366 and #367)

**Accepted within the local architecture review scope.** Reviewer: Astra (independent Opus 5.5 review agent, delegated by Alex).

- Scope: `fix/include-budget-and-properties`, base `c495d365` (#382 merged), head `45f40f6d` (two commits).
- This review rebinds the [#382 receipt](pr-382-memstore-portable-id-review.md) and keeps all of its assessments.
- It does not authorize a merge.

## Binding

- **Moved:** the Source and Validation digests. Validation moves through coverage counts only (13,440 calls analysed).
- **Unchanged:** Contract (`c70eaaf6`), analyzer, the Unknowns digest, the 313 UNKNOWN records and the 20 diagnostics.
- **Measurements:** 1,424 unresolved calls, 182 typing positions, 255 unknown positions, 0 violations.

## Source review

### #367: the include budget is checked before the parser

- `validate()` walks the literal include graph before `DescriptorParser` decodes any literal `.properties` include.
- It refuses only on the new `_IncludeBudgetExceeded`, a subclass of `_BoundedPolicyRefusal`, with a static message.
- Every other graph problem is left to the parser and to Build.

### #366: target placeholders resolve from project properties

- **At 36cfc6ba (blocked).** All `.properties` includes were merged order-free. Two probes Built `ready` while `datamimic run` failed with E007/I318 on `'{sink}'`:
  - a properties include placed after the step include;
  - a generate placed before its properties include.
- **At 45f40f6d, one ordered walk mirrors the parser and the runtime:**
  - a literal entry-level `.properties` include applies to the siblings after it and their subtrees, with a copy per scope, as in `dispatch.py`;
  - a step starts from the properties its include saw, as `include_task.py` parses it with `ctx.properties`;
  - a step's own `.properties` includes are ignored, because they fail at runtime;
  - an undefined name stays as written and gets DM401.
- **Build agrees with a real run on every probe.** Each line below is "Build outcome / `datamimic run` result":
  - properties before the step: ready / exit code 0;
  - properties after the step: DM401 at the step / I318;
  - generate before its include: DM401 / I318;
  - a property used only from a step file: DM401 / I201;
  - an undeclared target named by a property: DM401, with the value nowhere in the output / I312;
  - an include nested inside a generate does not leak to later setup siblings: DM401 / I204.

**Redaction.** No resolved value appears in any diagnostic or on stderr.

**Execution and binding.** Execution still gets the raw XML, and `sha256` binds the raw bytes. Analysis reads the resolved form.

### Placement and API

- `parse_properties` was already exported in `engine.dsl.api`, so the DSL API is not widened.
- The local placeholder pattern is the undotted subset of `dispatch.retrieve_element_attributes`. That is acceptable because `.properties` files are flat. A comment ties the two together.
- **Build order.** The include graph is now checked before the entry decompile. A graph or step-lint rejection therefore wins when both fail, and it is the more actionable one.

### Findings (not P1)

- **Low: re-serialisation drops what precedes the root.** `_analysis_xml` re-serialises a document only when a placeholder resolved in it. `etree.tostring(root)` then drops an XML declaration and any comments before the root, which can shift the line numbers in that document's decompile diagnostics. Lint findings keep the original line numbers, because they come from the in-place parse.
- **Info: a step included twice.** It is resolved once, under the first include's properties.

## Evidence boundary

**LOCAL VERIFIED (by this reviewer):**
- Source review.
- Build plus a real run for the six probes above, at both heads, and Build on the base.
- `test_property_targets` and `test_include_budget`: 8 passed.
- ruff.
- Native collection and the strict completion gate.

**NOT VERIFIED:**
- Full suites, and mypy at this head. The coordinator reports both clean.
- CI.

## Addendum: `05f3a085`, a step's own `.properties` include fails closed (Codex P2)

**Accepted.** After a literal `.properties` include inside a step, placeholders in the rest of that scope stay as written and are rejected with DM401. This also covers nested scopes and steps. The entry walk and later steps are unaffected.

**Correction to the 45f40f6d note.** It said a step's own `.properties` include fails at runtime. That was wrong. At runtime the file is read twice:
- **At parse time**, relative to the step's directory. That read decides the step's targets.
- **When the include task runs**, relative to the entry's directory. That file must exist too, or the run fails with I201.

**Probes.** Each layout gives the head Build, the `c2469bca` Build, and what `datamimic run` does. In each one, the step includes `override.properties`, with a copy next to the step and another next to the entry.

| Layout | Head (`05f3a085`) | `c2469bca` | `datamimic run` |
|---|---|---|---|
| Entry `sink=CSV`; step copy `sink=JSON`, entry copy `sink=XML` | DM401 | **ready, proving CSV** | writes `rows.json` |
| Entry `sink=CSV`; step's file defines only another key | DM401 | ready | writes `rows.csv` |
| No `sink` in the entry; step's file has `sink=CSV` | DM401 | DM401 | writes `rows.csv` |
| A step's properties followed by a later step that uses `{sink}` | ready | — | writes `rows.csv` |

- The first row is the Codex case: c2469bca proved a different target than the run writes, and the fix closes it.
- The last row shows a step's properties do not reach later steps, so analysis and runtime agree there.

**Why fail closed is the right call.**
- It never proves a target the runtime would not use.
- Following the step's directory would be more precise. It needs no change to `_literal_include_graph`: the step's directory is the parent of its uri, and the bounded child already reports a missing entry-relative copy as I201.
- But it would encode a two-path runtime rule that is itself questionable.

**The cost is false rejections.** The second and third rows are valid projects that are rejected. The second was `ready` at c2469bca.

**Low (follow-up).** DM401 does not say *why* a placeholder after a step-level `.properties` include is not proved. A dedicated remediation would tell the author to move the property to the entry.

**Binding.** Only the Source digest moves. Validation, Contract, Unknowns, the 313 UNKNOWN records and the 20 diagnostics are unchanged, as are the 1424/182/255 measurements.

**LOCAL VERIFIED:**
- Source review.
- The four probes, at the head and at c2469bca, with the real runs.
- `test_property_targets` and `test_include_budget`: 9 passed.
- ruff.
- The full gate.
