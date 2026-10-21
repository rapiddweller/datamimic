# Build includes architecture review (ADR #356 slice b1, PR #364)

**Accepted within the local architecture review scope.** Reviewer: Astra (independent Opus 5.5 review agent, delegated by Alex).

- Scope: `feat/build-includes`, base `287e9c87` (merged #362), b1 head `dab3bfc0` (`fbea1ad8` plus the Codex fixes `dab3bfc0`); the binding below is for slice b2 at `a4c9865a`.
- This review rebinds the [issue 361 receipt](issue-361-bounded-containment-review.md) and keeps all of its assessments.
- It does not authorize a merge and does not claim that every native rule passes.

## Current binding

| Item | Value |
|---|---|
| Source | `1db82bc8cbef8a6a1102bf1a0e2669526c0062a5ab0cdb0200288c9b0909ad26` |
| Target (unchanged) | `d83d4df102a2588a54598e26cb045b721cb024a118f51e31592b135050d4e78e` |
| Analyzer (unchanged; ArchKeel 4.0.1, Python 3.11.12) | `bb1a3262d3fdd38c3e9a6af980cc063281ae98ab1c28c89c2c5be6dfb450744f` |
| Validation | `3acc79e944ffb66a675ce1226c213590f21d18d2cfba8afdc39a5d7da7c5892c` |
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

## Codex fixes (`dab3bfc0`)

**DM407 per document: valid, fixed.**
- `CeBoundedExecutionPolicy.diagnostics` takes the other project documents.
- The delivery rule now applies to every document when any document in the graph exports to a buffered file exporter.
- Build passes the full project to the entry and to each step. The port signature is internal; a default keeps single-document callers working.
- The new test pins a targetless model product next to a delivery export.
- **Low (SPOT):** `_exports_to_file` repeats the file-export detection that `diagnostics` still computes for its own document. Calling the helper for the document too would leave one rule; the invalid-target diagnostic stays in the loop.
- Both count only `generate` products, as before.

**Aggregate include bytes: valid, fixed.**
- The walker counts all bytes read across the graph against a 64 MiB limit and raises the existing static bounded-limits refusal.
- It retains only `.xml` steps; `.properties` files are read for containment only.
- Peak memory is bounded by the aggregate limit plus one contained read, at most 100 MiB. That is acceptable for the authoring process.

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
- Source review of `287e9c87..dab3bfc0`.
- Producer-parity comparison.
- Producer/consumer order probes across steps.
- The `order_desk` fixture dry-run.
- 273 related tests passed: project build, dryrun includes, Build policy and workflow, library, containment, bounded executor, Build verification, acceptance, catalog, reference, `cli_v4`, trusted Python authoring.
- ruff and mypy are clean.
- At `dab3bfc0`: the related suites, 247 passed; ruff and mypy are clean; the calls profile is unchanged in unresolved calls (1,426).
- Native collection and a decoded call diff.
- Strict completion gate acceptance.

**NOT VERIFIED:**
- Full suites (the author reports unit+functional 3,244 and integration 608).
- CE CI.
- Windows.
- EE parity.

## Slice b2 (`57a956a4`, `9b61b234`)

**Accepted at `9b61b234`; `57a956a4` was blocked.**

What b2 adds:
- Build lints every included `.xml` step in the context of its project.
- The validator reports step findings at `("include", uri, xpath, "line", n)`.
- DM303/DM304 read the entry's `rngSeed`, so a step no longer repeats the seed findings.
- `include_task` scopes runtime descriptor identity to the step, so a bounded-run failure in a step is reported at `("include", uri, element, attribute)`. A missing step stays the entry's `<include>` error.
- The delivery rule is computed once over `(document, *project)`, which resolves my earlier Low.

**Blocked at `57a956a4` (Medium).** Step lint knew only the step and the entry. A memstore declared in another step was unknown to lint, although b1 treats memstores as project-wide (`dryrun.py:419`) and the runtime shares them.
- Reproduction: an entry includes `model/a.xml` (which declares the memstore and the producer) and `model/b.xml` (a targetless consumer), with identifier and foreign-key product roles.
- At b1 head `e9c9ab90`, Build was `ready`. At `57a956a4` it was rejected with DM402 at `("include","model/b.xml","/setup/generate","line",2)`.

**Fixed at `9b61b234`.**
- `LintContext.project` holds the entry and every step. `_declared_ids` unions all of them, and `run_root` is the entry.
- The same project now reaches `ready`; only the DM301 warning remains.
- The new test `test_memstore_declared_in_a_step_is_known_to_later_steps` pins the case.
- **Info:** the commit also carries three formatter-only hunks (`use_cases.py`, `schema_rules.py`, `script_semantics.py`).

**Redaction.**
- Step findings use the static rule explanation and fix hint, at structural paths with the literal workspace-relative uri.
- Runtime step failures project the title, the uri, the element and the attribute.
- No descriptor values appear.

**Info.**
- Lint unions declared ids without regard to declaration order. A store declared after its first use passes lint and fails at runtime; this predates b2 and is recorded in `delivery_boundary`.
- A malformed step file seen by the engine at runtime is named by its basename, because `DescriptorParser.parse` sets it. Bounded runs refuse malformed steps before parsing.

**Native result at `9b61b234`.**
- I re-collected the b1 head `e9c9ab90` independently, and it reproduces the previous receipt.
- Head:
  - 0 violations, failures [].
  - 1,426 unresolved calls, 178 typing positions, 256 unknown positions.
  - The 20 diagnostics are identical. Rules: 271 PASS and 5 UNKNOWN.
  - 314 UNKNOWN records, identical to the base.
- Calls: 13,269 analyzed; 1,426 unresolved and 2,030 partially resolved, both unchanged against b1. The decoded unresolved-call diff is empty.

**LOCAL VERIFIED:**
- The regression probe, before and after the fix.
- All 807 authoring unit tests passed, 4 skipped.
- 88 include-related unit and integration tests passed, 1 skipped.
- ruff and mypy (534 files).
- Native collection at head and base.
- Strict completion gate acceptance.

**NOT VERIFIED:**
- The full suites under `-n auto` (the author reports xdist contention in SQLite and the exporter matrix).
- CI.
- Windows.

### Addendum: `d002c133` (Codex threads on #365), accepted

**P1: the entry was linted standalone.**
- `validate` now lints the entry with `project=(entry, *literal steps)` through `_entry_project`.
- An unreadable graph falls back to standalone lint and stays refused by `include_graph` and by dry-run.
- An entry that reads a memstore declared in a step now builds `ready`. At `5abad9c4`, decompile already rejected it.
- **Cost:** one extra contained walk of the graph per `validate`. It is bounded by the 64 MiB graph limit. Build reads the graph again in `include_graph`, which is acceptable at this size.
- **Leakage:** none. The walk's errors are swallowed into the standalone fallback, and the project only adds declared ids to the union. Entry findings keep their own static texts and entry paths.

**P2: DM303 fired once per file.**
- DM303 now fires only where the run's seed is owned (`run_root is root`).
- A plain single file still reports DM303 (verified with `authoring lint`).
- An unseeded project reports it once, at the entry.

**Hidden entry errors (Info).**
- The union ignores order, so an entry that reads a step's memstore *before* including that step now passes lint.
- The bounded run still fails it. Build was rejected at the evidence phase with a child-execution failure, so Build never proves it.
- This extends the declaration-order gap recorded in `delivery_boundary`, which predates b2.

**Native result.**
- 0 violations; 1,426 unresolved calls, 178 typing positions, 256 unknown positions.
- The 20 diagnostics are unchanged; the 314 UNKNOWN records and their digest are unchanged.
- No change in unresolved or partially resolved calls.
- 809 authoring tests passed; ruff and mypy are clean.

### Addendum: `85724521` (Codex P2 on #365), accepted

**The fix.** When the include graph cannot be read, `_entry_project` now returns `complete=False`.
- DM401 then skips only its two undeclared-client and undeclared-target branches; target parse errors and unknown operations remain.
- DM402 skips only its undeclared-id branch; unsupported file suffixes remain.
- The real include refusal therefore surfaces in Build, instead of undeclared-id findings that the unread steps might resolve.

**Probes with `authoring lint`:**

| Case | Result |
|---|---|
| Single file with an undeclared target | DM401 |
| Entry with a readable step and an undeclared target | DM401 (`complete` stays True) |
| `.properties`-only include that is missing | Parse fails earlier with a descriptor error, so the flag is never reached |

So a readable graph hides no real undeclared id, and the single-file and no-include paths are unchanged.

**Redaction:** no new message. The change only suppresses findings.

**Smaller alternative (Low, not blocking).** For an entry with a malformed step, plain `authoring lint` now returns `ok: true`; only DM303 remains. Previously it returned DM401 noise.
- Build and dry-run still report the include refusal.
- Having `validate` emit that refusal itself when the walk fails would make lint honest about the cause.
- It would be no larger than the flag, and it would keep the INCLUDE-only Build result.

**Native result.**
- 0 violations; 1,426 unresolved calls, 178 typing positions.
- The 20 diagnostics, the 314 UNKNOWN records and the validation digest are unchanged; only the source digest changes.
- No change in unresolved or partially resolved calls.

**Tests:** 810 Authoring unit tests passed, 4 skipped; ruff and mypy are clean.

### Addendum: `a4c9865a` (Codex P2 on #365), accepted

The finding was valid. At runtime a step runs in a context copied from its parent, and the clients the step owns are cleaned up with it, not merged back. Lint now takes client ids from the file itself plus the entry (`project[:1]`); memstores stay project-wide.

I probed `include_graph` with a project whose entry declares `entrydb` and whose step `model/a.xml` declares `stepdb`:
- Step `a` targeting `entrydb` (the entry's client) passes.
- Step `a` targeting `stepdb` (its own client) passes.
- Sibling step `b` targeting `stepdb` is refused with DM401 at `("include","model/b.xml","/setup/generate","line",2)`.

**Info:** a step included *by another step* sees only the entry's clients and its own, not those of the step that includes it. Lint could therefore over-report there. Build already refuses step-declared clients in acceptance projection.

**Native result:**
- 0 violations; 1,426 unresolved calls, 178 typing positions.
- The 20 diagnostics and the 314 UNKNOWN records are unchanged.
- The validation digest changes only because one partially resolved call goes away (the dropped `el.get("id")` filter in the client comprehension): 13,274 analyzed, 2,029 partially resolved.

**Tests:** the project-build, public-lint and dry-run-includes suites pass; ruff and mypy are clean.

