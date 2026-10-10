# Amendment 20: semantic target freeze and delegated execution

Date: 2026-09-27. Source before this phase:
`3b844b5083e5af89269ef917bc0614601d30cf61`, including the existing uncommitted
recursive target draft recorded by the semantic-review manifest.

Alex delegates the remaining target decisions to Astra and authorizes
step-by-step implementation after that decision. This supersedes the previous
user-approval stop; it does not approve the incorrect Generator/StateMachine
placement or declare the target implemented.

## Responsibilities

- Astra decides semantic ownership and the complete shared CE/EE target.
- Luna implements bounded slices; Terra independently defines and runs QA.
- The coordinator integrates contracts, reviews changes and accepts each slice.

The existing semantic-review manifest and descriptor oracle remain historical
baselines. Do not regenerate them to hide changes. Target corrections must state
their semantic reason; implementation difficulty does not justify weaker rules.

## Acceptance

1. Freeze corrected responsibilities, physical destinations and contracts before
   moving production code. Every source has an explicit retained, moved, split
   or removed disposition; active initializers are not disposable scaffolding.
2. Preserve descriptor bytes and within-CE behavior. Verify seeded outputs with
   the same initial resource/target state; compare unseeded structure and
   declared invariants. Existing amendments remain applicable.
3. Reach the physical target without old-path shims, dependency cycles or
   unowned modules. Share future core paths with EE; do not claim EE itself
   refactored or import its runtime configuration or Rust implementation.
4. Verify the report from root to module: complete inventory, persistent
   component perspective, explicit file view, distinct history-back/parent-up,
   and target ownership independent of today's source grouping.
5. Report physical structure, contract conformance, behavior and delivery
   separately. A timeout or required UNKNOWN is not a pass. Identify the exact
   ArchKeel build; a local candidate is not the published 0.8.0 release.

No new product behavior is authorized by an architecture move. If a genuine
product conflict remains after Astra's review, preserve it as an explicit
blocker while progressing independent slices.
