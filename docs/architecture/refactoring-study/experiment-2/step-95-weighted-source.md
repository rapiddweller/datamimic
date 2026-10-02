# Step 95: weighted CSV result

2026-10-02. Base `f2479142`; published ArchKeel 0.8.4. Independent Luna tests
and implementation; fresh Astra source/specification/quality review PASS.

IO returns CSV text/null; Runtime still performs descriptor-type conversion.
The selected value, normalized weights, single Random.choices call, RNG state
and existing exception wrapper stay unchanged. No reader, registry, contract,
allowance, baseline, oracle, descriptor or gate changes.

CE5 contraction: an injected/private non-text result now raises the existing
outer ValueError with TypeError as cause. None and string subclasses retain
identity; external injected use is UNKNOWN. The first nonnumeric/empty weight
being treated as a header remains existing reader policy, not fixed here.

LOCAL VERIFIED: normal-plugin RED 5 expected failures/8 passes; new tests GREEN
13 passes. Unchanged Make units: 1634 passed, 11 unchanged skips, one existing
xfail and two existing warnings. Weighted/header/separator/guard/seeded replay
batch: 28 passes. Ruff, full MyPy (492 files), seven recursive definitions,
pinned Pylint executable-cycle checks and CLI/Python import smokes pass.

Eight unchanged descriptors ran: one seeded, seven unseeded, including one
expected error. Four Authoring projections match. Generic comparison remains
INCOMPLETE for the null-only active field; the parent-v-parent control fails
identically. Seven cases compare successfully; the existing permitted shape
variance is `csv_separatorr/test_weight_csv.xml`. Do not call this replay PASS.

Separate native acceptance passes on parent and candidate: the pre-existing
functional test requires 100 rows and every active value None. Both captured
case records are identical, including all field types/presence counts. Astra
approved this bounded checkpoint with the generic result still incomplete;
this is not permission to accept arbitrary null-only inferred shapes.

| Evidence | Parent f2479142 | Candidate |
| --- | --- | --- |
| Native exact-null case | step-95-baseline-weighted.log, PASS | step-95-root-weighted.log, PASS |
| Generic replay | step-95-parent-self-comparison.txt, incomplete | step-95-runtime-comparison.txt, incomplete |
| Captured counts/fields/presence | step-95-runtime-before.json | step-95-runtime-after.json, exact null-case match |

Candidate Python-source digest:
`f21100bba975e4d45422f8f0eaa8fc39c718968d5c3f90a3a08283c568acbf51`.

Fresh report: 104 -> 103 violations, 154 counted UNKNOWN unchanged. Only
VIO-e92ec2afeb36353b (WeightedDataSource.generate object return) disappears;
zero new finding/UNKNOWN IDs. Baseline-new fingerprints 68 -> 67, resolved 0.
492/492 files parse; no contract diagnostics. Global architecture remains FAIL.

CI-ONLY VERIFICATION: this checkpoint pending push. Parent CI completed with
architecture as its only failed job; E2E/release skipped. PR274 stays Draft.
Full 930-descriptor parity, historical capabilities parity, report navigation,
90% unit coverage, EE alignment and CE #282 remain open. No ArchKeel work.
