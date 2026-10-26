# Gate simplification review: bind the review to the contract, the analyzer and the UNKNOWN assessment

**Accepted, with one recommended addition.** Reviewer: Astra (independent Opus 5.5 review agent, delegated by Alex). I own the receipt.

- **Scope:** `ci/architecture-review-binding-simplified`, base `867f944c`, head `bff95949`.
- **Owner decision:** 2026-10-26.
- **Gate:** `make architecture-check` on this branch exits 0 (319 assessed UNKNOWN records). `test_completion_gate`: 37 passed.
- **No rebind:** the receipt format changed by deletion only.

## 1. What the deleted digests guaranteed

I classified every change of `completion-unknowns.json` on `development` since 2026-10-14 (32 changes, `git log` of the receipt). Each change compares one receipt version with the one before.

| What moved | Changes | Share |
|---|---|---|
| Only the source or validation digest | 16 | 50 % |
| UNKNOWN content only, with the same ids (`fact_ids`/`evidence_ids` re-issued, summary counts) | 10 | 31 % |
| UNKNOWN id set | 5 | 16 % |
| Contract digest | 5 | 16 % |
| Analyzer digest | 2 | 6 % |
| Assessed diagnostics | 2 | 6 % |

The last four rows overlap, because one change can move several things. Only 9 of the 32 changes (28 %) moved something the new gate still binds. The other 23 (72 %) were churn.

In my record-by-record checks (#394, #395, #396, the follow-up to #390), the same-id content changes were only re-issued `fact_ids` and `evidence_ids` and the position counts of summary records. I never saw a record keep its id and change its `reason`.

**The review, not the digest, found every real defect** in these rounds. The digests only forced a review to happen.

**One guarantee is lost: budget and baseline edits.**
- A change to `known-violations.json`, such as a raised `calls_unresolved` budget or an accepted baseline entry, made the validation digest move. A rebind was then required, and the receipt's `measurement_amendment` recorded the authorization (#381, #394).
- With this change, the gate passes after a budget raise with no review record at all.
- `known-violations.json` changed 8 times in its history, so binding it adds little churn.

**Recommended addition:** keep a `known_violations_digest` in the receipt. This means a hash of `known-violations.json`.

**Optional: bind the reason with the id.** The group check binds ids only. A record that kept its id and changed its `reason` would stay in a group that no longer fits. Binding `(id, data.reason)` pairs would catch this without the churn that the full record digest caused.

**Diagnostics stay bound.** The assessed diagnostics are still compared by content, so a changed diagnostic pointer still requires a record.

## 2. Kept checks

- Every kept check is reachable, and no message names a removed digest. The identity message now reads "Target and analyzer".
- No other tool in the repository reads the removed fields. The only remaining `source_digest` is in an archived experiment file.
- The `review_scope` history keeps its digest sentences. That is correct: they describe past states.

## 3. CONTRIBUTING.md

Correct the policy text as follows.

- **The UNKNOWN check.** "The code adds an UNKNOWN finding that the review record does not assess" is too narrow: a removed UNKNOWN also fails. Use: "The set of UNKNOWN findings differs from the set the review record assesses."
- **When a maintainer records a review.** "A maintainer records a review only when the UNKNOWN set, the contract or the analyzer changes" must also name:
  - a change of the validation diagnostics;
  - a change of `known-violations.json`, if the recommended binding is adopted. Otherwise, say that a budget raise needs a `measurement_amendment` entry by policy.
- **Where the review is recorded.** "Recorded as a review note in the pull request" is ambiguous. Say where: "a review note under `docs/architecture/refactoring-study/experiment-2/`, or an approving review on the pull request".
- **Style.** Write "Do not edit …", not "You do not edit …".

## 4. A new forcing function for source changes

The digest made a review mandatory. Replace it with these steps:

1. **CODEOWNERS plus branch protection** with "Require review from Code Owners". The owners must include the independent reviewer role. Cover `datamimic_ce/**`, `tests_ce/architecture/**`, `known-violations.json`, `Makefile`, `.github/**` and `docs/architecture/**`. The repository has no CODEOWNERS file today.
2. **A pull request template line:** "Independent architecture review: link to the review note or the approving review (required for `datamimic_ce/` changes)."
3. **The `known_violations_digest` binding from section 1.** Budget and baseline changes then keep a hard gate.

## Evidence boundary

**LOCAL VERIFIED:**
- Source review.
- The classification of the receipt history.
- Record-by-record UNKNOWN diffs from the earlier rounds.
- `test_completion_gate`.
- A clean full gate run.

**NOT VERIFIED:** the GitHub settings for CODEOWNERS and branch protection (recommendation only).
