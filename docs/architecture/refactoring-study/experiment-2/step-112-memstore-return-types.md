# Step 112: declare existing Memstore return types

Base: `2c298ee3`. Astra approves two annotations in `memstore.py`:
`consume -> None`, `sumEntityColumn -> int | float`. Executable bodies,
parameters, storage and contracts remain unchanged. Integral results stay
integers; fractional and nonfinite results stay floats. Native errors remain.
Independent Luna implementation and QA; Astra accepts the measured bounded slice.

LOCAL VERIFIED: **2,294 units passed, 11 skipped, one existing xfail**;
two existing Pydantic warnings. Twenty-six Memstore unit/integration/functional
checks, Ruff, full MyPy (491 files) and source formatting pass. Independent QA
adds exact numeric type checks (21 focused checks pass with standard pytest);
existing test-file formatting debt is untouched. Every function body
matches the preceding checkpoint; the other 490 source files are byte-identical.

Published ArchKeel **1.0.0** observes 491/491 files. Violations **89** remain
identical; measured UNKNOWN positions **202 -> 200**, with exactly two missing
return records removed and none added. Two cycle edges and 1,231 unresolved
calls remain. Strict architecture acceptance remains **FAIL**; no baseline,
checker, allowance or target changes.

Frozen 13-descriptor capture and four projections remain equivalent where
complete. The comparator retains the two incomplete captures and exits 1.
Supplemental unchanged tests pass before/after for XML import and seeded/unseeded
cascade; their success does not override the conservative cardinality oracle.
Historical capability baseline drift remains open. All inspected checkpoints
contain the same **931 tracked XML paths**; earlier 930 wording was inaccurate.

CI-ONLY VERIFICATION: no passing remote result claimed for this slice.
Full DSL parity, remaining UNKNOWN evaluation and report acceptance remain open.
Evidence: `/tmp/ce-resume-20261008/memstore-returns/` and
`/tmp/ce-resume-20261008/descriptor-audit.md`.
