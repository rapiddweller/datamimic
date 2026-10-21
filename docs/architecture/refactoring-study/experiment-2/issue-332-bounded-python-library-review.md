# Bounded Python library architecture review (issue 332, PR #360)

**Accepted within the local architecture review scope.** Alex decided the contract question (M1, Option A); `285e888b` implements it. `23080ad5` widens the builtin rule from calls to references.

- Reviewer: Astra (independent Opus 5.5 review agent, delegated by Alex).
- Scope: `feat/bounded-python-library`, base `f4e4de69`, head `23080ad5` (`d9d377bc`, the L1 fix `6e36e1c5`, the M1 contract change `285e888b`, and the builtin-reference rule `23080ad5`).
- This review rebinds the [issue 357 receipt](issue-357-seeded-script-imports-review.md) and keeps all of its assessments.
- It does not authorize a merge and does not claim that every native rule passes.

## Current binding

| Item | Value |
|---|---|
| Source | `5b64e910deaabe19f2b5f049ebfb8822f653be8becb1ad640d7363096cd32ed8` |
| Target (unchanged) | `d83d4df102a2588a54598e26cb045b721cb024a118f51e31592b135050d4e78e` |
| Analyzer (unchanged; ArchKeel 4.0.1, Python 3.11.12) | `bb1a3262d3fdd38c3e9a6af980cc063281ae98ab1c28c89c2c5be6dfb450744f` |
| Validation | `c4cbf04796207b4f81c524fce6613244e1b46d301eb91e75058094319da13514` |
| UNKNOWN | `eedde60f12fc785fc81f3044cbe020929e0c5f18b912a458d04a2d6057c46a6d` |

Budgets are unchanged: 1,431 unresolved calls, 178 typing positions and 256 unknown positions. No ArchKeel policy, architecture contract, baseline, gate or `measurement_amendment` change. The published DSL contract changes additively (see M1).

## What changed

```
Build (DM JSON)                         bounded child (XML)
CeBoundedExecutionPolicy                neutralize_for_dry_run (dryrun.py:529)
  execute at document/root/children/N     root executes: membership in root_stmt.sub_statements (:541)
  strategy dispatch (:60): PYTHON_LIBRARY   included XML: _validate_bounded_includes (:374), entry rngSeed
  + _is_bounded_python_library (:21)
        |                                       |
        +------ admits_python_library (script_semantics.py:156): python, no target, no script
                python_library_refusal (:174) on the exact source -> _BoundedPolicyRefusal (dryrun.py:286)
Build: seeded document + any execute -> deterministic replay forced (build.py:87)
ExecuteStatement.language / normalize_python_source (execute_statement.py:18, :28): one owner for parser and task
```

Since `285e888b`, the registry publishes `execute` with the bounded strategy `PYTHON_LIBRARY` (`registry.py:238`, `dsl_element.py:31`). The policy, the workspace snapshot (`bounded_executor.py:329`) and include validation (`dryrun.py:374`) dispatch on that strategy.

## Answers to the review questions

### 1. Admission soundness

Admission is correct. I probed each case on `d9d377bc` and re-ran the probes on `285e888b` and `23080ad5`; everything outside a setup-level Python library was refused or failed loudly:

| Probe | Result |
|---|---|
| `<execute>` inside `<if>` at setup level | Parser rejects |
| Include of a step with `<execute>` inside `<generate>` | `side_effect` refusal "only as a setup-level Python library" |
| `uri="lib/{libname}.scr.py"` | Not interpolated at parse or run time; runtime "Task Execute Script Not Found" |
| `uri` plus inline text | Parser rejects |
| `type="python"` with a `.sql` uri | The static check skips unparseable source; runtime fails with the same SyntaxError |
| SQL, bash, `target=`, `script=`, nested | Stay `unsupported_bounded_operation` (PR tests) |
| Non-UTF-8 library | The check skips it, and the runtime decodes with the fixed `utf-8` default and fails too |

The check reads the uri relative to the entry directory (`path.parent`), which is the directory the native runtime uses for included contexts. Build refuses XML includes, so in Build only an entry descriptor can carry a library. Bounded dry-run covers included steps.

### 2. Re-reading the file (TOCTOU)

Acceptable.
- The check reads the library from the private workspace snapshot in the bounded child, before any task runs. `ExecuteTask` reads the same snapshot later.
- Only code that already runs inside the child could change the file between the two reads.
- Because the check is not a sandbox (see below), the second read creates no new capability.
- Possible later simplification: hand the checked source to the statement so the runtime does not read the file again.

### 3. Redaction

Acceptable. Refusals contain only static rule text, a line number and the uri basename.
- The uri is descriptor-authored and not property-expanded, as the placeholder probe showed.
- Basename-only matches the existing CLI convention.
- The PR test `test_refusal_names_the_earliest_line_and_no_source_text` pins the absence of source text.

### 4. Forced replay

The semantics are correct and fail safe.
- A seeded entry library with a module-level `random.randint` draw is rejected after the forced replay, with mismatch `first_difference: 0`.
- An unseeded library does not replay (`not_requested`).
- Policy refusals report the forced gate as `blocked`.

**Finding L1 (Low): resolved in `6e36e1c5`.** At `d9d377bc`, a failed forced replay was reported as "Bounded execution or a requested verification gate failed." with generic field advice.
- Build now adds a static evidence diagnostic only when the replay failed and the caller had not requested it (`build.py:159-167`). The message names the likely cause (a module-level draw in the library) and echoes no value.
- Re-probed:
  - Forced replay with a module-level draw: rejected with the new message only.
  - Requested replay: keeps the generic message.
  - Seeded library: `passed`.
  - Unseeded library: `not_requested`.
- New fixture: `library_module_level_draw.xml`.
- **Residual Info:** the diagnostic keeps the VALIDATION rule's generic remediation ("Correct the reported field, discriminator, or graph reference."), because `catalog_diagnostic` takes no remediation. The message itself carries the cause.

### 5. Placement

**`python_library_refusal` / `admits_python_library` in `authoring/domain/script_semantics.py`:** cohesive. The module already owns static script checks that give authoring scripts an unambiguous runtime meaning. Policy, the bounded child and Build share it, which keeps one source of truth for the rule.

**`requires_deterministic_replay` (`:149`):** arguably a Build verification rule. The author keeps it in `script_semantics.py` because moving it to `domain/proof.py` would give `proof.py` new DM-JSON and engine imports. I accept that: it is a placement preference (**L2, Info**), not a cohesion defect.

**M1: resolved in `285e888b` (Alex decided Option A).** At `d9d377bc`, the published `execute` capability still said `unsupported` while Build admitted Python libraries. Now the strategy is published as `python_library`:
- `capability --domain element --name execute` reports `bounded_execution.strategy: "python_library"`.
- DM JSON schema `x-datamimic-bounded-strategy` counts are container 9, counted 3, neutral 13, python_library 1, unsupported 2.
- The new test `test_published_execute_capability_names_the_library_strategy` pins it.
- **All enum consumers handle the new value.** They are the policy (`:60-62`: None/UNSUPPORTED refuse; PYTHON_LIBRARY refuses unless setup-level Python), the snapshot rule (`:329`, unchanged effect for `execute`), include validation (`:374`, UNSUPPORTED still refuses at `:389`), and the publishers (catalog, DM JSON codec). Nothing else branches on the enum.
- Dropping the `EL_EXECUTE` tag check from the predicate is safe, because only PYTHON_LIBRARY elements reach it.
- Behaviour is unchanged: the admission probes and the forced-replay probes give the same results.
- **Downstream pinning.** No golden pins the strategy:
  - The contract bundle computes its file hashes at export time.
  - The bundle envelope keeps `schema_version: "1"`. The change only adds an enum value, but a consumer that validates against a closed set of values must learn it.
  - EE (`origin/development` `3e7456a90`) has its own `BoundedExecutionStrategy` with different values (`pass_through`, `dependency`, `expand`, `reject`, `side_effect`) and no CE mapping. So no EE contract test can pin this.
  - Recommendation: record the CE→EE vocabulary difference on datamimic-ee#73 when the parity work drafts a mapping.

### 6. ArchKeel

I re-collected base `f4e4de69` independently, and it reproduces the previous receipt. Head:
- 534/534 files; `failures` is empty.
- 0 violations, 0 baseline additions or resolutions.
- Rules: 271 PASS and 5 UNKNOWN.
- The 20 diagnostics are identical. The full report exits 0. Contract and analyzer are unchanged.

**Calls:** 13,069 → 13,139; resolved 9,636 → 9,693 (the L1 `catalog_diagnostic` call, the strategy dispatch and the reference rule); partially resolved 2,002 → 2,015; unresolved 1,431 → 1,431.
- Every unresolved difference is a move into `ExecuteStatement`, from the parser's `_resolve_type` and the task's `_normalize_python`.
- The 13 new partially resolved calls are new authoring reads (`node.get`, `properties.get`, `module.split/startswith`, `refusal.message/remediation`) plus the moved `_EXT_TYPE.get`/`code.replace`.
- No call was promoted.

**UNKNOWN records:** 314, with identical identities.
- Four records changed only fact and evidence references, after line shifts: the `ExecuteStatement` surface, `get_model_class`, `get_element_definition` and one DSL facade route.
- The DSL-API-TYPES summary now reads 318 decided of 397 positions (was 313/392): the five new declared positions are all decided, and undecided stays 79.

## Builtin references (`23080ad5`, Codex P1)

The finding was valid: only direct calls were refused.
- `REFUSED_NAMES` now refuses any `ast.Name` reference to open, exec, eval, compile, `__import__`, `__builtins__`, globals, locals and vars.
- `REFUSED_ATTRIBUTES` refuses `__builtins__`, `__globals__`, `__code__`, `__subclasses__` and `__dict__`.
- I confirmed the reported paths are now refused: `write = open`, `__builtins__['open']`, `f.__globals__`.
- Dropping `input` and `breakpoint` is acceptable: neither reads files nor builds code.

**Remaining bypasses (Info).** These pass the check:
- `getattr(f, '__globals__')`, with the name as a literal or a concatenated string;
- `random.__loader__.get_data(...)`, a file read through an admitted module;
- `pd.read_csv`, `pd.eval`, `typing.ForwardRef`, `logging.FileHandler`, `numpy.ctypeslib`.

**Recommendation, not blocking:**
- Fold two cheap cases into the existing rule: `getattr`/`setattr`/`delattr` with a string-constant name in `REFUSED_ATTRIBUTES`, and the attributes `__loader__`/`__spec__`. Both match the rule's own intent at near-zero false-positive cost.
- Do not try to list module APIs. They cannot be closed by name, and pretending otherwise turns a lint into false assurance.

**False positives (Low).** These are refused:
- `from re import compile` followed by `compile(...)`;
- `self.__dict__` in a serialization helper;
- a parameter or local named `vars` or `open`.

The remediation text for these cases ("Pass data in from the model instead of reading files...") is misleading. `__dict__` is the broadest entry; `self.__dict__` is a common library idiom. Two options:
- keep it, and name `dataclasses.asdict` in the remediation; or
- replace it with a refusal of the string constant `'__builtins__'` used as a subscript or `getattr` key.

The corpus did not hit any of these (39 unseeded and 24 seeded scripts pass, per the author), so this is a preference.

**Included libraries in Build (Codex P1, second thread).** Not reachable today, as the author says: Build rejects `library_included.xml` as `unsupported_bounded_operation`, with replay `not_requested`. When Build starts admitting includes, the replay requirement must be decided over the resolved include graph.

## Security note (pre-existing, outside this PR)

The library check is an admission rule, not a sandbox. The PR documents this.
- Admitted modules can still touch files: for example `pandas` `read_csv`/`to_csv`/`read_pickle` and `logging.FileHandler`.
- `getattr` with a string name and module attributes such as `__loader__` bypass the reference rules (see above).
- Existing bounded expressions have the same exposure. On this head, a dry-run key `pd.DataFrame({'a': [1]}).to_csv('<absolute path outside the workspace>')` wrote the file.
- So bounded dry-run and Build do not prove the absence of file side effects for script code. The receipt's `delivery_boundary` records this; it deserves its own follow-up rather than a change in this PR.

## Evidence boundary

**LOCAL VERIFIED (by this reviewer):**
- Source review of `f4e4de69..23080ad5`.
- Admission, placeholder, encoding, forced-replay, mismatch, redaction and capability probes.
- Native collection at head and base; decoded call and UNKNOWN diffs.
- ruff and full mypy (534 files) at `d9d377bc`, `6e36e1c5`, `285e888b` and `23080ad5`.
- 196 tests passed: bounded Python library, dryrun includes, trusted Python authoring (functional), bounded executor, Build verification, dryrun, determinism scenarios and `extensive_script`.
- At `6e36e1c5`: bounded Python library, Build verification and acceptance tests, 115 passed.
- At `285e888b`: bounded Python library, build policy, CE catalog, dynamic count, reference, transport architecture, contract bundle, dryrun includes, bounded executor, trusted Python authoring and public API ownership tests, 152 passed. Capability and schema strategy counts were checked directly.
- At `23080ad5`: bounded Python library, dryrun includes, trusted Python authoring and build policy tests, 65 passed. Probed 17 bypass and false-positive cases against `python_library_refusal`. Re-probed Build for the seeded library, the module-level draw and the included library.
- Strict completion gate acceptance.

**NOT VERIFIED:**
- Full unit, integration and functional suites (the author reports 3,079/608/122 passed).
- CE CI.
- External services and Windows.
- EE parity.
