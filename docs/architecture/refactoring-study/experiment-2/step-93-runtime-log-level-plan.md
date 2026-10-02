# Typed Runtime log level Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Follow the tasks below; independent QA owns tests, implementation owns production code.

**Goal:** Keep transport argument parsing outside the typed Runtime request.

**Architecture:** DataMimic retains its args parameter and resolves the existing logging semantics. RunRequest carries log_level: int = logging.INFO; Runtime configures logging from that value. No new helper, enum, module or configuration layer.

**Tech Stack:** Existing Python, stdlib logging/dataclasses, pytest and Make.

**Spec:** docs/architecture/inner/target.md; protocol.md in this directory. Astra's source-based recommendation is retained in test-artifacts/ce-after92-next-runtime-slice-astra.md.

## Global Constraints

- Base 26ed7f6b; isolated CE worktree; published ArchKeel 0.8.4. No ArchKeel implementation.
- Preserve DataMimic(args=...) and existing logging fallback/error behavior; keep process bootstrap → title → logger order inside Runtime.
- No descriptor, oracle, baseline, permission, gate, skip, xfail, dependency or unrelated primary-edit changes.
- Keep public script contexts and native properties/captures; this does not solve their remaining violations.
- Direct RunRequest(args=...) is an internal CE 5.0 contraction under the approved no-shim target; external direct callers remain UNKNOWN.
- Root reviews and commits/pushes only the slice to the existing Draft PR274; no merge or force-push.

## Review Focus

- None/missing log_level: INFO, not an environment-derived default.
- Unknown names/non-string values: INFO; no str() coercion or broader exception suppression.
- Registered custom names: preserve the stdlib integer, including lowercase input.
- Repeated sessions: preserve existing logger-handler behavior, not a logging redesign.
- Invalid descriptor or unexpected conversion error: preserve the exception; best-effort process-title side effects may occur later for invalid adapter inputs.

### Task 1: Independent compatibility tests

**Files:** tests_ce/unit_tests/test_python_api/test_runtime_boundary.py; tests_ce/unit_tests/test_util/test_process_util.py.

**Interfaces:** Consumes current DataMimic/RunRequest/RuntimeRunSession; produces tests for a typed integer boundary while preserving Python args input.

- [x] Independently inspect the existing flow before implementation; save expected behavior and concerns outside tracked product files.
- [x] Update the request forwarding expectation to log_level=logging.DEBUG and the process-order test to use a real RunRequest.
- [x] Add a parameterized adapter-to-real-runner check: None/missing/unknown/non-string→INFO, lowercase DEBUG→DEBUG, registered custom name→its integer. Observe setup_logger input; keep unrelated args out of RunRequest. Pin default integer annotation/field and removal of args.
- [x] Preserve existing process-order, live-capture, invalid-path and error tests; add one narrow check that an unexpected conversion exception propagates and repeated real logging setup keeps the existing handler behavior. Do not clone whole fixtures or duplicate unrelated tests.
- [x] Run the two focused files before implementation; record expected RED failures. Root accepts the independent first pass before production edits.

### Task 2: Typed input, adapter resolution and evidence

**Files:** engine/runtime/contracts.py; interfaces/python/datamimic.py; engine/runtime/lifecycle/runner.py below datamimic_ce. Root owns this plan and step-93-runtime-log-level.md.

**Interfaces:** RunRequest.log_level: int = logging.INFO replaces args. DataMimic's args signature stays unchanged; RuntimeRunSession consumes the integer.

- [x] Read real callers; move the existing name resolution into DataMimic before constructing RunRequest. Catch only AttributeError, keep int results, otherwise INFO. No new wrapper or reflective lookup.
- [x] Replace the Runtime request field/import; pass request.log_level directly to setup_logger. Preserve Runtime bootstrap/title/logger ordering and all descriptor execution/capture behavior.
- [x] Run focused tests GREEN and self-review the three-file diff. Do not edit QA tests, contract permissions or other files; report before committing.
- [x] Root runs Make test-unit, lint, typecheck, architecture-definition-check and architecture-cycle-check; captures a fresh report/against validation without weakening the existing global FAIL.
- [x] Root compares six unchanged selected descriptors (two seeded, four unseeded) and Authoring projection hashes before/after with the existing oracle. No full-corpus claim from selected checks.
- [ ] Astra performs scoped specification/code-quality review. Root records the direct-constructor change and verification limits, commits/pushes the reviewed slice, regenerates separate committed/IDE reports and updates PR274.

No permission amendment is planned. If the published checker blocks this specific safe change, reproduce/file the ArchKeel issue and stop; never silently widen the contract.
