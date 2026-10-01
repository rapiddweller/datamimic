# Step 79: state-machine definition ownership

The immutable `StateMachineDef` now belongs to the existing Domain generation
contract. The walker, Runtime cache, declaration precedence and RNG are unchanged.
Registry separation stays deferred: a supported XML converter reads
`root.generators[id].start`. Named-alias reuse remains [issue #279](https://github.com/rapiddweller/datamimic/issues/279).

LOCAL VERIFIED: consumer RED before the move; 1,540 clean-snapshot unit passes
(11 skipped, 1 xfailed); 13 focused owner/generator tests; four integration tests;
Ruff, MyPy (491 files), Pylint executable-cycle check, five recursive-definition
and four inner-target checks. Ten deterministic captures match frozen BEFORE;
the original unseeded state-machine capture differs, with its
count/key/state/transition invariants preserved. An additional private seed-17
copy matches all 340 rows exactly. Cold-process deepcopy/dill continuation
matches the next 20 values, with the canonical class verified in each child.
This is not full multiprocess-engine proof or a rerun of the full DSL oracle.

Released ArchKeel 0.8.1 still reports clean FAIL 110 / counted UNKNOWN 157, the
same as Step 78. Dirty integration remains 102 / 155. Neither is target acceptance.
[Amendment 83](amendment-83.md) records the exact internal export promotion.
The Makefile now pins released 0.8.1 rather than historical Git source so CI
requests the same checker. No baseline, budget, tracked descriptor or oracle changed.

Independent Luna implementation and QA; Astra approved the bounded product move.
CI-ONLY VERIFICATION: not yet run for this checkpoint. Full architecture, DSL
oracle gaps and report projection defects remain open; no merge or release.
