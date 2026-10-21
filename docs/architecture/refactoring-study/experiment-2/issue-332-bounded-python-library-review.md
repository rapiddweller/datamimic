# Bounded Python library architecture review (issue 332, PR #360)

**Accepted within the local architecture review scope. One open contract decision is for Alex.**

- Reviewer: Astra (independent Opus 5.5 review agent, delegated by Alex).
- Scope: `feat/bounded-python-library`, base `f4e4de69`, head `d9d377bc`.
- This review rebinds the [issue 357 receipt](issue-357-seeded-script-imports-review.md) and keeps all of its assessments.
- It does not authorize a merge and does not claim that every native rule passes.

## Current binding

| Item | Value |
|---|---|
| Source | `b6bdbb58414227474fd4f45ad72ce3247f563e8145c3c1fe0f8b422e71fb4459` |
| Target (unchanged) | `d83d4df102a2588a54598e26cb045b721cb024a118f51e31592b135050d4e78e` |
| Analyzer (unchanged; ArchKeel 4.0.1, Python 3.11.12) | `bb1a3262d3fdd38c3e9a6af980cc063281ae98ab1c28c89c2c5be6dfb450744f` |
| Validation | `5fd80037de332824b1fcecb80e8e98f4cb581d370c3ed6a75c8940662aa6f756` |
| UNKNOWN | `8c982d6811d77dc23ce8a4731380aea17a8f4b2aa71a548a9f45175adb8a163f` |

Budgets are unchanged: 1,431 unresolved calls, 178 typing positions and 256 unknown positions. No policy, contract, baseline, gate or `measurement_amendment` change.

## What changed

```
Build (DM JSON)                         bounded child (XML)
CeBoundedExecutionPolicy                neutralize_for_dry_run (dryrun.py:529)
  execute at document/root/children/N     root executes: membership in root_stmt.sub_statements (:541)
  + admits_python_library  (:21, :67)     included XML: _validate_bounded_includes (:372), entry rngSeed
        |                                       |
        +------ admits_python_library (script_semantics.py:156): python, no target, no script
                python_library_refusal (:174) on the exact source -> _BoundedPolicyRefusal (dryrun.py:286)
Build: seeded document + any execute -> deterministic replay forced (build.py:87)
ExecuteStatement.language / normalize_python_source (execute_statement.py:18, :28): one owner for parser and task
```

The registry's bounded profile for `execute` stays `UNSUPPORTED`. Only the policy admits the setup-level Python subset.

## Answers to the review questions

### 1. Admission soundness

Admission is correct. I probed each case on `d9d377bc`; everything outside a setup-level Python library was refused or failed loudly:

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

**Finding L1 (Low):** a failed forced replay is reported as "Bounded execution or a requested verification gate failed." (`build.py:182`), with a generic field/discriminator remediation.
- It was not requested, and the remediation does not point at the probable cause.
- Recommendation: give it a static reason, for example "seeded model loads Python: a draw at module level, a default argument or an unlisted import is not seeded".

### 5. Placement

**`python_library_refusal` / `admits_python_library` in `authoring/domain/script_semantics.py`:** cohesive. The module already owns static script checks that give authoring scripts an unambiguous runtime meaning. Policy, the bounded child and Build share it, which keeps one source of truth for the rule.

**`requires_deterministic_replay` (`:149`):** a Build verification rule rather than a script rule. It would sit more naturally next to `BuildVerificationOptions` in `domain/proof.py`. **L2 (Low)**, not a layout amendment.

**M1 (Medium, decision for Alex, not blocking):** the published `execute` capability is now inaccurate.
- `datamimic authoring capability --domain element --name execute` still reports `bounded_execution.strategy: "unsupported"`, but Build admits setup-level Python libraries.
- The plugin reference `ce.md` describes the admission, so the two sources disagree.
- The disagreement is conservative: an agent that trusts the contract avoids `<execute>`.
- Making the contract say what Build does needs a contract and registry amendment. That is a scope decision to raise with Alex, not something to work around in code.

### 6. ArchKeel

I re-collected base `f4e4de69` independently, and it reproduces the previous receipt. Head:
- 534/534 files; `failures` is empty.
- 0 violations, 0 baseline additions or resolutions.
- Rules: 271 PASS and 5 UNKNOWN.
- The 20 diagnostics are identical. The full report exits 0. Contract and analyzer are unchanged.

**Calls:** 13,069 → 13,136; resolved 9,636 → 9,690; partially resolved 2,002 → 2,015; unresolved 1,431 → 1,431.
- Every unresolved difference is a move into `ExecuteStatement`, from the parser's `_resolve_type` and the task's `_normalize_python`.
- The 13 new partially resolved calls are new authoring reads (`node.get`, `properties.get`, `module.split/startswith`, `refusal.message/remediation`) plus the moved `_EXT_TYPE.get`/`code.replace`.
- No call was promoted.

**UNKNOWN records:** 314, with identical identities.
- Two records changed only fact and evidence references (`ExecuteStatement` surface).
- The DSL-API-TYPES summary now reads 318 decided of 397 positions (was 313/392): the five new declared positions are all decided, and undecided stays 79.

## Security note (pre-existing, outside this PR)

The library check is an admission rule, not a sandbox. The PR documents this.
- Admitted modules can still touch files: for example `pandas` `read_csv`/`to_csv`/`read_pickle` and `logging.FileHandler`.
- `__builtins__` lookups bypass the builtin-call rule.
- Existing bounded expressions have the same exposure. On this head, a dry-run key `pd.DataFrame({'a': [1]}).to_csv('<absolute path outside the workspace>')` wrote the file.
- So bounded dry-run and Build do not prove the absence of file side effects for script code. The receipt's `delivery_boundary` records this; it deserves its own follow-up rather than a change in this PR.

## Evidence boundary

**LOCAL VERIFIED (by this reviewer):**
- Source review of `f4e4de69..d9d377bc`.
- Admission, placeholder, encoding, forced-replay, mismatch, redaction and capability probes.
- Native collection at head and base; decoded call and UNKNOWN diffs.
- ruff and full mypy (534 files).
- 196 tests passed: bounded Python library, dryrun includes, trusted Python authoring (functional), bounded executor, Build verification, dryrun, determinism scenarios and `extensive_script`.
- Strict completion gate acceptance.

**NOT VERIFIED:**
- Full unit, integration and functional suites (the author reports 3,079/608/122 passed).
- CE CI.
- External services and Windows.
- EE parity.
