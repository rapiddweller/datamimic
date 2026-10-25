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
