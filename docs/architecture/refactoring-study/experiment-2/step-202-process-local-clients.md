# Step 202 — process-local descriptor clients

**Accepted scope:** descriptor-owned PostgreSQL/Mongo source/helper transfer and
target writes in SINGLE/spawn. This implements Amendment 199's bounded client
path; it does not establish universal client or DSL compatibility.

Source commit: `54dde04aac147ee4a4ae03d23b434d50022dd07a`.
Its production and test trees equal independently reviewed isolated `8703aad6`.
Setup stores typed configurations, then binds before consumer construction.
Three worker graphs retain the observed registered/default/closure identity split;
receivers construct and clean up local clients. Includes preserve parent resources.
Caller-owned injections remain outside owned cleanup. Context stays passive.

| Native case | Actual executor / spawned workers | Verdict |
|---|---|---|
| PostgreSQL SINGLE | 64609 | PASS |
| PostgreSQL MP | 65302 [0,3), 65301 [3,6) | PASS |
| MongoDB SINGLE | 65834 | PASS |
| MongoDB MP | 65926 [0,3), 65927 [3,6) | PASS |
| Original PostgreSQL target | 66069, 66070 | FAIL: table `written` not found |
| Original MongoDB target | none | NOT RUN after failure |
| Corrected-profile PostgreSQL target | 67006 [0,3), 67005 [3,6) | PASS |
| Corrected-profile MongoDB target | 67072 [0,3), 67071 [3,6) | PASS |

The original six-case batch remains failed. A separate two-target packet changes
only fresh resource names and PostgreSQL's profile schema to match its owned
schema. No production fix or original-case retry occurs. The unchanged profile
merger overwrites explicit descriptor attributes; offline conflict/empty-profile
controls establish that behavior. Environment property files are the preferred
connection-configuration source. [CE #291](https://github.com/rapiddweller/datamimic/issues/291)
tracks documentation/UX clarity, not a proven need to change conflict precedence.

Four original source cases and two corrected targets retain six ordered native
rows/types, helper counts and Step 201 aliases. Each MP receiver constructs its
registered and callable clients locally; target exporters use local registered
sinks. Native target readback equals capture. All started process groups are gone
and reaped; all owned schemas/collections are absent. Independent raw QA accepts
this combined bounded scope, preserving the original failure.

[Receipt](step-202-process-local-clients-receipt.json) pins both packets, QA and
local logs. Native generator graphs were empty; nonempty generator/reducer/cache
interception is separately covered by unit sentinels. The frozen runtime source
equals the source commit. The later persistent service test is additional; one
unit file's trailing blank line was removed with identical AST.

LOCAL VERIFIED: 2370 unit passes, 11 skips, one expected failure; two later cleanup
cases verified separately. Final transfer/scope run: 24 passes. Six permanent
service regressions and two existing PostgreSQL sequence regressions pass. Ruff,
full-package MyPy (488 files), 13 definition checks and executable-cycle check
pass. ArchKeel: 13 unchanged semantic violations, 200 scalar UNKNOWNs,
488/488 parsed, `declared_rules: FAIL`. No corpus-ledger promotion.
CI-ONLY VERIFICATION: pending for this source/evidence delivery.

Ray processes, arbitrary/injected captures, persisted pickles, general socket/
object-graph isolation, transitive driver code and remaining DSL/EE scope remain
UNKNOWN. Dependency permissions and forbidden predicates are unchanged.
