# Step 204 — native distribution owner profiles

Independent SPEC/QUALITY GO admits **eight exact owner-profile rows**:
the DSL ledger becomes **174/931 reviewed, 757 UNKNOWN**. This is bounded
compatibility evidence, not full DSL or target acceptance. No production code,
descriptor, owner test or architecture permission changes in this step.

Native executions compare original `a219163e533d661bcc7bda0faa5ecc77909ab5aa`
with `9e6667e105dcf436ccd15c334b977bc6442e390e`. They were not executed at
primary `1adb6cee624f66a602eb033c83d1cf597c6cad9a`: its separately checked
bridge changes only `read_variable_query`'s return annotation. Executable AST
is equal after removing that annotation; annotation introspection and external
static consumers remain UNKNOWN.

All fixtures below live in `tests_ce/integration_tests/test_key_native_distribution/`.

| Descriptor | Exact observed behavior per endpoint |
|---|---|
| `test_native_distribution.xml` | Two complete seeded captures, 400 rows each; five fields and native types agree. |
| `test_sequences.xml` | Two complete seeded captures, 70 rows each; product order and counts 5/8/12/10/30/5 agree. |
| `test_sequence_exhaustion.xml` | Three ordered rows 1/2/3 despite requested count 5. |
| `test_distribution_without_range.xml` | Missing-range error graph and diagnostic agree. |
| `test_distribution_wrong_type.xml` | Same missing-range error; numeric-type guard coverage remains unproven. |
| `test_distribution_unknown_value.xml` | Unknown-distribution error graph and diagnostic agree. |
| `test_sequence_mp_rejected.xml` | Multiprocessing rejected before workers start. |
| `test_sequence_mp_rejected_nested.xml` | Nested multiprocessing rejected before workers start. |

There are **16 once-only native owner calls, 20 engine executions, 48 passing
pytest phases**, ten complete captures containing 1,886 rows across endpoints,
five capture pairs and five error-graph pairs. All children returned exit 0.
Complete output bytes, type trees, product/row order, error cause/context,
stdout, stable phase logs and owned cleanup were checked. The audited runs
observed no service connections, process launches or worker serialization;
the rejection cases do not prove successful multiprocessing.

## Retained harness failures

Prelaunch environment mismatch and interpreter-created pycache caused early
setup failures before any native owner ran. Versioned bootstrap and anonymous
plugin-identity amendments preserve those failures and all raw collections.
These are experiment harness defects, not CE or ArchKeel defects.

The producing v3 parents remain literally **six PASS and ten
FAIL_RETAINED_NO_RETRY**. All ten failures arose when the comparator treated
pytest's cumulative teardown stderr as new output. Read-only v4 acceptance
requires teardown stderr to equal call stderr byte-for-byte, no setup
diagnostics, the sole pinned assertion failure, passing native phases and
unchanged source/audit/cleanup evidence. Frozen v3 must reject the same receipt
at its exact assertion site; same-label plugin equality is checked separately.
Six positive and fifteen negative controls pass. No native owner was retried
and no raw failure was rewritten.

## Admission and findings

The accepted ledger changes exactly eight rows. The other **923 raw lines are
byte-identical**. Existing changes are limited to input/isolation review fields;
historical, oracle and c992 evidence remains unchanged. Independent acceptance
authorizes only the eight new evidence statuses to become
`ACCEPTED_EXACT_OWNER_PROFILE`. [Receipt](step-204-native-distributions-receipt.json)
pins the baseline, candidate, accepted ledger, reviews and producing artifacts.
Raw packets remain local under `/private/tmp/ce-step204-native-distribution-20261010`.

- [CE #292](https://github.com/rapiddweller/datamimic/issues/292): the
  non-numeric fixture also lacks a range, so its broad regex never proves the
  numeric-type guard. Isolate that guard without changing validation order.
- [CE #293](https://github.com/rapiddweller/datamimic/issues/293): model-level
  validation renders `None:` instead of a useful field-free diagnostic.

Both observations are reproduced at both native endpoints; fixes are separate
from this compatibility experiment.

LOCAL VERIFIED: eight native pairs, independent raw-evidence review and GO,
status-only ledger admission, source bridge, Ruff and full-package MyPy
(488 files). Step 203's 2399 unit passes remain prior evidence on unchanged
executable source; that suite was not rerun here.

CI-ONLY VERIFICATION: [run 38069660474](https://github.com/rapiddweller/datamimic/actions/runs/38069660474)
at exact `1adb6cee` completed. Its returned first page contains 24 successful
jobs, two architecture failures and two skips. Runtime suites, service tests,
build/wheels, determinism, Ruff and MyPy pass. Architecture validation still
reports **12 violations and 200 scalar UNKNOWNs**; the local canonical count
remains **254 UNKNOWN records**. Report exit 0 is not target acceptance.
This documentation commit needs its own CI.

Skipped: native retries, full-suite rerun and production fixes for #292/#293.
Remaining risks: standalone exporter safety, universal OS/dependency closure,
interrupted cleanup, successful multiprocessing, statistical semantics,
frozen-oracle parity, the other 757 descriptors and full CE/EE target acceptance.
