# Build includes architecture review (ADR #356 slice b1, PR #364)

**Accepted within the local architecture review scope.** Reviewer: Astra (independent Opus 5.5 review agent, delegated by Alex).

- Scope: `feat/build-includes`, base `287e9c87` (merged #362), head `fbea1ad8`.
- This review rebinds the [issue 361 receipt](issue-361-bounded-containment-review.md) and keeps all of its assessments.
- It does not authorize a merge and does not claim that every native rule passes.

## Current binding

| Item | Value |
|---|---|
| Source | `cf401224fd17ed41249dfc7d5dd6e5e2f9fa06e19fd3e8a877ed7bb2a29172e6` |
| Target (unchanged) | `d83d4df102a2588a54598e26cb045b721cb024a118f51e31592b135050d4e78e` |
| Analyzer (unchanged; ArchKeel 4.0.1, Python 3.11.12) | `bb1a3262d3fdd38c3e9a6af980cc063281ae98ab1c28c89c2c5be6dfb450744f` |
| Validation | `5e00b93c3a127eced603b6e4306e6f5224aab650078117f3c64a1af2ec0a3cf7` |
| UNKNOWN | `2ab5f7a323140bb3c632ca77b59cb26288f438e215800f44bc66c90d77a3e676` |

**Budgets:**
- `calls_unresolved` is ratcheted **down** from 1,429 to the measured 1,426. That tightens the budget and authorizes nothing; `measurement_amendment` says so.
- `typing_positions` stays at 178 and `unknown_positions` at 256.
- No contract, gate or other policy change.

## Design

```
Build parent                                        bounded child
compile entry                                       _validate_bounded_includes (dryrun.py:380)
validator.include_graph (validator.py:114) ---+       |
   contained workspace reader                 |       +-- _literal_include_graph (dryrun.py:334)  <- one walker
   _literal_include_graph -------------------+          check every element (#360 library check, unsupported refusal)
decompile steps, policy per step                        graph-wide memstore producers
requires_deterministic_replay(entry, steps)          neutralize_for_dry_run: graph producers (:607, :650)
project_acceptance(request, entry, steps)
```

- One walker serves both sides, so the rules are identical.
- Nested URIs resolve against the entry directory on both sides, which is also how the runtime resolves them.
- Each side reads through its own contained reader: the parent through the bound workspace, the child through its snapshot.

## Review questions

### 1. Producer facts and completeness

**Parity with the statement-based producers.** I compared the graph producers against `_memstore_producers` on the same tree. Both give the same `(store, entity, product)` facts. The tree covered:
- a top-level producer;
- a nested producer with `targetEntity` and a multi-target list;
- a producer inside `<condition><if>`;
- an `<iterate>` with `type`.

**Order.** Producer step then consumer step proves the consumer `exhausted`, fully read. Consumer step then producer step fails the run; it is not proven complete.

**A producer that never runs:**
- It is still counted as a producer.
- Its own capture is incomplete, because observed rows are fewer than requested.
- So the consumer stays unproven, as in the single-file logic.

**`{prop}` in a target:** the literal is not a declared memstore id, so the consumer stays unbound. This errs on the safe side.

**Duplicate product names** across steps are refused.

### 2. Parent/child parity

The parity holds:
- the same walker;
- the entry-relative URIs;
- both reads are contained;
- a missing or outside file is a static refusal on both sides.

### 3. Redaction

- Step URIs appear in paths, such as `("include", uri, ...)`. They are literal, descriptor-authored, workspace-relative structure, like the descriptor path itself.
- Refusal texts are static.

### 4. TOCTOU

Acceptable for b1, because the PR states it.
- The parent reads step files for acceptance, and the child reads its snapshot.
- A Ready Build does not yet record which step bytes it proved. `IncludedDescriptor.sha256` (`requests.py:55`) is computed but not consumed.
- Binding is slice (c). The receipt's `delivery_boundary` records this.
- **Low:** either consume the digest in (c) or drop the field until then, so it isn't dead data.

### 5. Contract

- **Not a widening:** the new port method (`DescriptorValidator.include_graph`), `IncludedDescriptor`/`IncludeGraphResult` and `Diagnostic.relocated`. They are internal to Authoring, and ArchKeel shows no violation and no contract change.
- **Published change, Info:** the `include` bounded strategy changes from `unsupported` to `neutral` with its `uri` dependency (`registry.py:228`). This follows ADR #356's direction decision.
  - Unlike `execute`'s `python_library`, `neutral` does not say that only literal, setup-level, contained includes are admitted.
  - The refusals are explicit, so the conservative risk is small.
  - Worth one line of confirmation from Alex in the PR, because it changes a published value.
- **Low:**
  - `validator.py` imports `_BoundedPolicyRefusal`/`_literal_include_graph` from `dryrun`, and `build.py` imports `_codec_diagnostic` from `use_cases`.
  - Reusing them keeps one source of truth, but the names are private.
  - Publishing them under non-underscore names would make the shared ownership explicit.

### 6. Security

No regression.
- Steps pass through the same per-element checks in the child, including the #360 library check and the unsupported-element refusal.
- They are also policy-checked in the parent.
- The #362 containment applies to the whole child run, and step files belong to the protected snapshot.
- Forced replay now covers Python anywhere in the graph.

## Native result

- **Base:** I re-collected base `287e9c87` independently, and it reproduces every digest of the previous receipt.
- **Head:**
  - 534/534 files; failures [].
  - 0 violations, 0 baseline additions or resolutions.
  - Rules: 271 PASS and 5 UNKNOWN.
  - The 20 diagnostics are identical, and the report exits 0.
- **Calls:** 13,190 → 13,247; resolved 9,744 → 9,792; partially resolved 2,017 → 2,029; unresolved 1,429 → 1,426.
  - Removed: two `uri.endswith`, the include-detection `endswith`, and one `getparent`.
  - The `getparent` reappears in the shared walker.
  - The new partially resolved calls are new reads in the walker, the validator and Build.
- **UNKNOWN records:** 314, with identical identities. Two records have reference churn only, and `UNKNOWN-PYTHON-DYNAMIC-CALLS` changes to 1,426.

## Evidence boundary

**LOCAL VERIFIED (by this reviewer):**
- Source review of `287e9c87..fbea1ad8`.
- Producer-parity comparison.
- Producer/consumer order probes across steps.
- The `order_desk` fixture dry-run.
- 273 related tests passed: project build, dryrun includes, Build policy and workflow, library, containment, bounded executor, Build verification, acceptance, catalog, reference, `cli_v4`, trusted Python authoring.
- ruff and mypy are clean.
- Native collection and a decoded call diff.
- Strict completion gate acceptance.

**NOT VERIFIED:**
- Full suites (the author reports unit+functional 3,244 and integration 608).
- CE CI.
- Windows.
- EE parity.
