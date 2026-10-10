# Step 118 — supplemental descriptor evidence

Ten additional reviewed XML paths were captured at checkpoint `12d5e3a5` and
candidate `c65d0090`. All ten records match: four seeded digest captures and six
unseeded outcome/count/shape captures. Overall acceptance remains **FAIL**.

## Scope and execution

[The receipt](step-118-descriptor-receipt.json) records exact paths, input hashes,
commits, observed counts, capture hashes and comparator result. These ten paths
are disjoint from the original 13 selected paths. The original capture remains
10 CAPTURED, one EXPECTED-ERROR and two UNVERIFIED; it was not replaced or upgraded.
`12d5e3a5` is a supplemental checkpoint, not the original pre-refactor baseline.

Astra and independent Luna reviewed the inputs before execution: finite local
CSV sources, relative JSON/XML outputs and time windows; no external clients,
includes, custom hooks, absolute/traversal paths or script IO. The existing
recorder staged each fixture directory in a temporary directory and checked its
source import root. Staging is not an OS sandbox; input inspection was required.

The baseline used a detached scratch local clone, with the same project Python
3.11.12 environment as the candidate. No linked worktree or existing checkout
was reset. The unchanged recorder ran serially with explicit argument lists:
`--jobs 1 --capture-only --only` the ten receipt paths. Both runs returned 0;
each retained the complete 931-path inventory and exactly ten CAPTURED records.
Root independently verified result sets, inventory equality and output hashes.

Independent QA ran exactly twelve selected owner-test nodes in each scratch
clone: **12 passed before, 12 passed after**. These check roundtrip pagination,
header/value preservation, source-length collision, unique selection and replay,
decimal JSON types, JSON export location and time-series count/order/replay;
the XML-template test checks completion. Decimal's test also scaffolds its
committed one-row model. No additional tracked XML fixtures were executed.
Pytest ran serially with only its rerun-failures plugin disabled after that
plugin's sandbox socket failure before collection. Every selected test ran once;
no test failure was excluded or converted into a pass.
QA left the environment implicit. Root repeated the same twelve nodes per clone
with explicit clone import roots, `RUNTIME_ENVIRONMENT=development`, serial
execution and standard plugins: **12 passed before, 12 passed after**.

## Preserved failure

The unchanged comparator returned **1**: ten descriptors compared, one
capabilities-projection difference, zero normalized/optional-shape variances.
Compiler and both reference projections match. The capability JSON has exactly
two differing leaves:

- `schema_version`: `4.3.1.dev246+dirty` → `4.3.1.dev288+dirty`.
- `elements.execute.attributes.target.description`: Step 114 restored the
  original SQL-method wording; the earlier checkpoint contains the removed text.

No metadata, description, oracle or baseline was changed to make this comparison
pass. `--capture-only` preserves raw projection drift; its exit 0 is not acceptance.

## Remaining acceptance

These captures establish only the ten reviewed paths at these checkpoints.
Unseeded records compare observed counts, shapes and field presence, not exact
values. Dependencies were shared, not independently frozen. The recorder does
not execute caller-test assertions; XML-template caller coverage checks completion
only. Full 931-descriptor parity, service-backed lanes, unsupported export formats,
the two incomplete original captures and historical projection gates remain open.

LOCAL VERIFIED: ten matching supplemental captures and twelve owner tests per
checkpoint, with independent input, capture and projection counterchecks.
No production, descriptor, contract, frozen capture or oracle changed.
CI-ONLY VERIFICATION: these supplemental captures have no dedicated CI proof;
the prior exact-commit CI receipt is recorded in Step 117.
