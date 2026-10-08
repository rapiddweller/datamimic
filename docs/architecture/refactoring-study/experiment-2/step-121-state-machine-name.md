# Step 121 — state-machine name contract

`StateMachineStatement` already requires `name: str`. Its getter now promises
`str`, and its existing assignment explicitly types `_name` as `str`.
The parser supplies the required model ID; no body, validation, storage,
base-class contract, descriptor or oracle changed. Getter introspection
intentionally changes. EE's graph representation is not transferred.

An isolated full-package probe rejected the proposed mixed-registry annotation
with three errors. Narrowing only this getter also failed: inherited `_name`
remained optional. The approved two-annotation correction passed all 491 files.
No cast, wrapper, suppression or contract exception was added.

## Evidence

At dirty HEAD `29610097`, **16 existing cases passed before and after**:
four state-machine owner tests and 12 parser cases. The three complete raw
captures are byte-identical; the unchanged comparator reports three compared,
zero differences and zero tolerated normalizations. All four projections match.
These are local before/after checks, not original-control acceptance.

The owner tests exercise named registration, legal walks, weighted branches and
seed replay. They do not directly assert the getter or missing/empty model IDs.
Seeded capture digests match; explicit runtime row counts are not recorded for
those captures. Fresh scratch directories and explicit import/development
settings were used; remaining environment was inherited. No service or file
target appears in these descriptors.

Independent QA verified the two-line footprint, executable AST/bytecode and
ordinary instance/pickle state under controlled valid and wrong-typed inputs.
Passing `None` outside the existing typed constructor contract still returns
`None`; no runtime enforcement was introduced.

Ruff, full-package MyPy, changed-file formatting, executable-cycle checking and
eight architecture-definition tests passed. The fresh pinned report retains
**89 violations, 254 canonical UNKNOWNs, 200 measured UNKNOWN positions and two
measured cycle edges**. Full finding/module arrays match the preserved packet.
That earlier packet keeps its actual dirty `6433321f` metadata; it is not a
fresh observation of the pre-edit HEAD. The new source digest is `a87c6685…`.

[The receipt](step-121-state-machine-receipt.json) hashes the retained evidence.
The frozen capability expectation mismatch, mixed-registry debt, report
navigation gap and broader DSL proof remain open. Full acceptance remains FAIL.

LOCAL VERIFIED: 16/16 cases per phase; three unchanged captures/projections;
package/static checks and architecture guards; independent source/receipt review.
CI-ONLY VERIFICATION: this source slice has not yet run in CI. The preceding
`29610097` runs finished with 24 successful jobs, two architecture failures and
two skips each; those results do not verify this edit.
