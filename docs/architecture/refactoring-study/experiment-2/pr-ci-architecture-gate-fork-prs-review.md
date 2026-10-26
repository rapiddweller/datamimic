# Architecture gate for fork pull requests: review

**Accepted within the local architecture review scope.** Reviewer: Astra (independent Opus 5.5 review agent, delegated by Alex).

- **Scope:** `ci/architecture-gate-fork-prs`, base `9005e143`, head `8e2c1ac7` (two commits).
- **Owner decision (2026-10-26):** pull requests from forks run the substance of the gate only. The owner accepts the residual risk that a maintainer merges a fork pull request without the review record; `development` then turns red.
- **Binding.** This branch changes no file under `datamimic_ce`, and the full gate passes on it unchanged. The receipt is therefore not rebound.

## Review

**1. The split is complete.**
- `check_substance` keeps every check that needs no review: failures, observation and coverage, report completeness, the shape of the validation exit and diagnostics, violations and baseline drift, the unfiltered report, and the UNKNOWN evidence class.
- `check_review_binding` keeps only the review identity: the digests, `reviewed_by`, the diagnostic assessment and the group assessment.
- The full mode runs both parts, so it checks exactly what it checked before. Only the order of the messages changed.

**2. Mode selection fails closed.**
- Only `github.event.pull_request.head.repo.fork == true` selects the substance step. The two `if:` conditions are complementary.
- Push (branches and tags) and `workflow_dispatch` have no `pull_request` payload, so they run the full check.
- A deleted fork gives a null `head.repo`, so it runs the full check and stays red.
- The workflow has no `pull_request_target` or `merge_group` trigger. Review the condition again if one is added.

**3. The fork controls its own gate.** A `pull_request` run uses the fork's own workflow, Makefile, `completion_gate.py` and budgets, so a fork result is advisory only. The authoritative backstop is the full check on pushes to `development`.

That backstop cannot catch a merged change to the gate itself, because it runs the merged files. Examples:
- a weaker `completion_gate.py`, `Makefile` or workflow;
- raised budgets in `known-violations.json`;
- an edited receipt.

Repository rules must protect these paths. The repository has no CODEOWNERS file.

**4. CLI.**
- `--substance-only` works only as the first argument. In substance mode the receipt path is ignored.
- An unknown flag, the flag in a later position, or missing paths fails with exit code 1 (probed).

### Findings

- **Low: an environment variable can weaken the gate.** `COMPLETION_GATE_FLAGS ?=` takes its value from the environment. `COMPLETION_GATE_FLAGS=--substance-only make -n architecture-check` expands to the substance-only command. Use `COMPLETION_GATE_FLAGS =` instead: a command-line assignment still overrides it, and an environment variable does not.
- **Low: CONTRIBUTING accuracy and style.**
  - Item 2 does not mention a measurement budget overrun. Add "or exceeds a measurement budget".
  - The maintainer steps start with "for each pull request that changes `datamimic_ce/`". The record also binds the architecture target, `known-violations.json` and the analyzer version. Say instead: "when the full check reports that the review does not match".
  - Simplified Technical English puts a warning before the step it affects. Move the warning above step 5.
  - Use the active voice in step 2, for example: "Ask the independent reviewer to record the review in …".
- **Recommendation:** add a CODEOWNERS file or branch rules that require a maintainer review for `tests_ce/architecture/**`, `Makefile`, `.github/**`, `known-violations.json` and `docs/architecture/**`.

## Evidence boundary

**LOCAL VERIFIED (by this reviewer):**
- Source review.
- `test_completion_gate`: 50 passed.
- A clean full gate run on this branch: exit 0.
- Six probes of the CLI arguments, with their exit codes.
- The `make -n` probe of the environment override.

**NOT VERIFIED:**
- GitHub Actions behaviour for real fork, deleted-fork and `workflow_dispatch` events. The analysis above is from the expressions only.
