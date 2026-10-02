# Step 43: group generator definitions

Move the three named-generator DSL models into `model/setup/generators/`.
`model/setup` now has seven direct children. No compatibility module or new
runtime layer was added; the matching EE location remains a target only.

Independent QA found no stale imports. The wheel contains all three moved
modules. Three state-machine descriptors and all four authoring projections
are identical to Step 42. Local gates: 1,471 unit tests passed (11 skipped,
1 xfailed); nine architecture-definition tests, Ruff, full-package MyPy,
and the Pylint import-cycle gate passed. ArchKeel observed all 490 files with
the same 123 violations and 194 UNKNOWNs as Step 42. CI and the full
descriptor corpus were not run for this move.
