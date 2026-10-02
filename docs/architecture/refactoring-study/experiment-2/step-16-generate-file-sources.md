# Step 16: Generate file sources belong to IO

Runtime still resolves the statement and evaluates source templates. IO now
classifies `<generate source=...>`, selects the file reader, and applies the
file window. The boundary takes resolved scalar values, not a runtime context
or statement. Amendment 59 declares the already-used DSL `EL_GENERATE` token
at this crossing. No descriptor was edited.

Independent Luna implementation and QA passes preceded root review. QA added
positive and negative cases for weighted CSV, DBUnit offset/name fallback,
non-file sources, and JSON/XML template behavior. Root review caught an
undeclared DSL import in the first draft; the final candidate has no forbidden
component edge. The new IO operation exposes heterogeneous source rows as
`list[dict]`. ArchKeel reports this as one new `IO-API-TYPES` finding; a type
wrapper would not make arbitrary source columns statically known, so it remains
visible rather than being hidden by a cast or baseline increase.

The pre-step package was archived from `e604155e`. Ten selected XML files had
identical SHA-256 bytes in both trees. With the corrected unseeded shape
comparator, nine selected descriptors matched old/new, including seeded CSV
and JSON and the expected weighted-CSV error. The unseeded XML-only output
descriptor remained `UNVERIFIED` in both trees: the oracle does not capture an
XML output schema. An unseeded JSON case had initially differed only in the
random count of an optional nested field. Repeated old-code runs also varied;
the comparator now checks field names, types, and required/optional status,
not that random frequency. Negative tests reject requiredness and type changes.

LOCAL VERIFIED: 1,360 unit tests passed, 11 skipped, 1 expected failure;
552 integration tests passed, two skipped, and the one socket-blocked SSE test
passed when rerun with a local socket; 133 functional tests passed. Focused
source tests: 70 passed. Ruff, full-package mypy (487 files), Pylint cyclic
imports, five target-definition checks, four inner-contract checks, and
`git diff --check` passed. The candidate report has 487 observed modules and
487 exact module targets with no missing responsibility, 147 component
responsibilities, no dependency violations, and 126 type findings.

CI-ONLY VERIFICATION: not run. The standard ArchKeel 0.8.0 gate cannot parse
the current recursive declarations (`contract.declarations fields mismatch`).
The local report candidate evaluates the contract but returns `UNKNOWN` from
13 inherited-public-interface warnings and 93 baseline-new findings. Full
descriptor parity, service-backed evidence, and final target acceptance are
still open. This step is behavioral progress, not completion of the target.
