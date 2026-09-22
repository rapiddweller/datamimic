# Experiment 2 protocol

Written before implementation. Contract edits after freeze require a dated amendment explaining
why the original target was wrong; an implementation difficulty is not a reason to weaken it.

## Fixed inputs

| Input | Frozen value |
|---|---|
| Code | `development` at `a219163e533d661bcc7bda0faa5ecc77909ab5aa` |
| Worktree | `/private/tmp/datamimic-architecture-experiment-2` |
| Branch | `experiment/target-architecture-v2` |
| Architecture checker | ArchKeel `0.6.0`, local tag `d14035b31ef2addac9cfea738a70d8643df2f7ae` |
| Implementation agent | Luna, contract and baseline read-only |
| Verification agent | Luna, production code and contract read-only |
| Remote changes | none |

## Acceptance contract

1. `archkeel validate --baseline known-violations.json` never accepts new debt.
2. Final `archkeel validate` passes without a baseline and reports no material UNKNOWN.
3. The exact root layout and component namespaces match `target-architecture.md`.
4. Every component crossing uses its declared API and every API has checked boundary types.
5. All existing XML descriptors still parse. Seeded descriptors produce byte-identical captured
   output. Unseeded descriptors retain outcome, product counts, row counts, and value shapes.
6. Authoring schema, reference, capability, compiler, lint, and transport projections remain
   identical unless an explicitly approved product change is recorded.
7. Existing public CLI commands and documented Python entry points remain importable.
8. Unit, API, factory, functional, integration, architecture, lint, and full-package mypy gates
   pass. External-service tests run serially against already-running local services.

## Per-step gate

1. smallest coherent architecture slice;
2. targeted test;
3. descriptor and projection comparison for affected paths;
4. ArchKeel baseline decreases and never grows;
5. relevant broader suites, then `make lint` and `make typecheck`;
6. diff review, experiment log, one local commit.

The serial result is authoritative when xdist and serial execution disagree. No flaky descriptor is
excluded from equivalence until repeated unchanged Step-0 runs demonstrate the instability and the
evidence is logged.

When the first real function is added to an API module, the same commit adds that module's
`boundary_types` rule. The rule then remains mandatory. This is a narrowing, not permission to
change the target.

## Agent separation

- The implementation agent changes production code and targeted tests for one approved slice.
- The verification agent builds the Step-0 oracle, runs gates, and reports regressions. It does not
  repair production code.
- The orchestrator owns the contract, baseline, slice selection, acceptance, and commits.

## Success and stop conditions

Success means the target is reached, not merely that debt decreased. Stop and report instead of
weakening the target when behavior cannot be proven, ArchKeel returns UNKNOWN for a required fact,
or compatibility requires a product decision.

## Known checker limit under test

ArchKeel 0.6.0 can require target namespaces only after they exist as scanned packages. The freeze
therefore adds empty target package markers before Step 0. It also returns `UNKNOWN` for
`boundary_types` until a real facade function exists; those rules are activated with the first
real function instead of adding dummy code. Both constraints are recorded as checker limits, not
accepted architecture debt.

Layout violations on an empty legacy `__init__.py` also lack the non-empty excerpt ArchKeel later
requires for its own trace. The freeze adds ownership-only docstrings to the affected files so the
same violations become traceable and baselineable.

Target progress may remove a legacy package from a component's ownership list or promote a built
API from `planned` to `public`; these are synchronized contract facts, not target changes. A target
permission or restriction changes only through an amendment.
