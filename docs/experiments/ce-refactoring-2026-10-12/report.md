# Evidence-governed CE refactoring: retrospective case study

12 October 2026. DATAMIMIC Community Edition. Archive edition 1.

## Finding

The CE refactoring reached its agreed structural acceptance rule: complete
observation, zero declared violations, and an explicit independent agent
assessment of every remaining UNKNOWN. The final acceptance names 286 UNKNOWN
records. It does not turn them into PASS.

The behavioral evidence is a classified join over 931 XML inputs. The evidence
combines native owner scenarios, parser comparisons, negative contracts,
authoring diagnostics, service readbacks and CI-only cases. These are different
proofs. The input count is neither 931 independent experiments nor 931 fully
successful runtime replays.

The record supports a substantial engineering case-study report now. A scientific
paper is plausible after a focused related-work review, human methodological
review and a durable artifact deposit. It does not support a controlled claim
about productivity, model superiority, cost savings or defect freedom.

## Case and boundaries

The starting source is development commit
`a219163e533d661bcc7bda0faa5ecc77909ab5aa`. The delivered source is
`384b7723d950d8b312b1080d23ffd89a5343c9b0`. Documentation archival changes after
that commit do not constitute another runtime experiment.

The engineering goal was to make ownership explicit down to meaningful inner
components, move CE towards that physical structure, and preserve the declared
DSL behavior. Source observation, declared Target, and their differences needed
separate report navigation. The architect retained policy decisions; agents
implemented and reviewed bounded changes.

CE is a Python data-generation engine with XML descriptors, domain models and
generators, file/database IO, runtime orchestration, and authoring/CLI/MCP
interfaces. The target groups the execution code below `engine/{dsl,runtime,io}`;
keeps `domains` and `authoring` explicit; separates transport adapters; and moves
packaged demos below `resources`. Public dependency and type boundaries are
machine checked. The physical and semantic target is reviewed separately from
behavioral compatibility.

The reviewed process also records worker-local client creation: the executor
process creates clients, including the main process when it is the single
executor. Parallel parents pass a small configuration context rather than live
clients. Environment property files are the preferred CE system configuration.
The SQL dispatch exception preserves approved dynamic-client compatibility and
native errors. These are concrete architecture decisions, not inferred from a
zero-violation result.

EE acceptance, deployment, merge readiness and every possible output behavior
are outside this acceptance. Python module paths were intentionally relocated;
legacy import shims were not promised by the approved target. This report does
not redefine that as universal Python API backward compatibility.

## Study design

This is a retrospective analysis of one industrial refactoring intervention.
The research questions below were formulated during archival analysis. They
were not preregistered experimental hypotheses.

1. What evidence was needed to accept a declared target while keeping uncertainty
   visible?
2. Which provenance failures made apparently successful compatibility checks
   invalid, and how were they detected?
3. How can a final input-level evidence join distinguish successful execution,
   expected rejection, approved change, existing debt and unavailable services?

The engineering protocol was written before implementation. It froze a source
revision and an initial checker. Subsequent target amendments, checker changes
and acceptance decisions are recorded. Those changes mean that a longitudinal
violation count is not a measurement under a single fixed instrument.

The frozen protocol asked for zero material unknown positions. During final
closure, the architect explicitly clarified the acceptance rule as “0 Verstöße,
verbleibende UNKNOWNs unabhängig bewertet.” The final GO uses that rule and
bounded behavioral evidence. It must not be presented as satisfying the stronger
original zero-UNKNOWN or universal-parity reading. This policy clarification is
part of the study, alongside the technical changes.

Runeson and Höst describe case studies as investigations in their real context,
with traceable evidence and explicit validity limitations. Their distinction
between observational studies and interventions is relevant here: the
participants actively changed both the product and its checking tool. We use
“retrospective case study” descriptively; a paper should have a human methods
review rather than retroactively label this a controlled experiment.
[Methodological reference](https://link.springer.com/article/10.1007/s10664-008-9102-8).

## Evidence and chronology

| Checkpoint | Recorded evidence | Interpretation |
|---|---|---|
| 22 September | Experiment-2 target/protocol frozen; initial ArchKeel 0.6.0 | Engineering starting procedure, not today's final instrument |
| 23–24 September | 474/474 files observed; zero violations under 0.6.1; separate raw UNKNOWNs and open DSL comparisons | Earlier bounded structural verdict; broader behavior still open |
| 8 October handoff | ArchKeel 1.0.0: 491/491 files, 91 violations, 202 measured UNKNOWN positions | Expanded/evolved target and analysis expose further work |
| 11 October | ArchKeel 2.0.0 adopted; zero violations with reviewed UNKNOWN policy | Structural acceptance and behavioral closure remain separate |
| 12 October | 488/488 files; 0 violations; 286 assessed UNKNOWN records; final 931-input join; Astra GO | Final bounded CE acceptance |

The intermediate numbers have different Source, Target and analyzer identities.
They must not be drawn as one monotonic “bugs removed” curve. In particular,
zero under an earlier instrument and 91 under a later one are not a demonstrated
regression. The final source has 488 observed Python files; review records also
cover packages and components. Those populations must not be added together as
independent source files.

The machine receipts bind Source, Target, analyzer and payload hashes. Final
identities recorded by the acceptance are:

- Source digest: `81f86023ad58442a08dd77cf72e9524a24c91b0466aa46645b732cc4f393d428`.
- Target digest: `289d6c0ee28d75e53e7ed8d057edbd66dd4004c5c362b6cccf5f7c095e0f7745`.
- Analyzer digest: `7106e3595fa7df9269cb43ee280f9c557659db7bda171b1f65ff5619ab54aa24`.

These identify the retained acceptance packet, not a guarantee that regenerating
an observation in a changed environment produces byte-identical reports.

## Final behavioral results

The mutually assigned final input classes sum to 931:

| Proof class | Inputs |
|---|---:|
| Paired native owner scenario | 666 |
| Paired expected-rejection owner scenario | 42 |
| Paired negative owner contract | 70 |
| Paired direct outcome/export contract | 32 |
| Included in a passing root runtime/readback | 8 |
| Paired service runtime/readback | 2 |
| Paired copied-fixture owner contract | 9 |
| Paired authoring diagnostic contract | 41 |
| Paired pre-existing error | 12 |
| Approved behavior change | 1 |
| Non-standalone asset or malformed fixture | 17 |
| Unused debt | 11 |
| Disabled legacy fragment | 3 |
| CI module owner only; locally unavailable | 17 |
| **Total** | **931** |

All 931 parser comparison rows agree in their recorded classification: 914 setup
inputs and 17 non-setup classifications. Parser agreement is not runtime or
output equivalence. The 70 individually checked negative contracts establish
expected rejection on both pinned revisions, including exception-class and
owner-message checks. Their success means that rejection was correct.

The 41 authoring fixtures yielded matching diagnostic tuples and message
fingerprints, with 59 diagnostics on each revision. That evidence comes from
the authoring linter. It does not claim native generation for those fixtures.
Nine XLSX input/copy correspondences retain exact hashes and owning tests rather
than treating a copied filename as proof.

The final independent review checked the indexed hashes, reconstructed the
666 native-owner success rows, examined rejection contracts, source origins,
JUnit accounting and sample outputs, and re-executed the completion policy on
the retained payloads. “Independent” here means a separate agent task with a
bounded review assignment. It is not an external human replication or an ACM
artifact-evaluation award.

| Suite evidence | Original | Delivered |
|---|---:|---:|
| Ordinary local integration/functional tests | 676 effective passes, 2 skips | 706 passes, 2 skips |
| Available local service tests | 152 effective passes, 10 skips, 6 profile failures | 158 passes, 10 skips, 6 profile failures |
| Exact-head CI service aggregate | 164 passes, 4 skips | 170 passes, 4 skips |

“Effective” totals include explicitly recorded successful retries. The original
ordinary run initially had one socket failure; its isolated retry passed. The
original service total includes three MySQL retries after the disposable service
was available. Initial failure receipts remain history. Test totals changed;
these columns are not a fixed-population statistical comparison.

CI sources:
[original run](https://github.com/rapiddweller/datamimic/actions/runs/35588158288),
[delivered run](https://github.com/rapiddweller/datamimic/actions/runs/38181877757).
The 17 locally unavailable vendor/stage inputs have module-level CI evidence,
not individual old/new payload captures.

Ecommerce and large-file runs compare counts, schemas, sampled types and asserted
constants. Their generated values are unseeded, so byte equality was not the
acceptance oracle. Matching samples do not prove identical distributions or
every possible value. Earlier 43 typed-equal capture pairs remain attributed to
their earlier candidate revisions; they were not promoted to exact-final replay.

## Provenance failures and corrections

A crucial failure was mixed import provenance. An editable-install finder could
load current modules while the top-level package appeared to come from the
original checkout. Checking only the package root was insufficient. Early
“original” parser, direct-run and service receipts are therefore VOID. Corrected
runs use the real legacy APIs, remove the editable finder and assert the origin
of every loaded CE module. Invalid receipts are retained alongside their
invalidation; archival must not silently delete this failure mode.

Grouped negative runs timed out. Their partial outcomes were superseded by
individual bounded native checks. An interrupted service run was superseded by
completed durable JUnit. Neither interruption is relabelled as a successful run.

The immutable historical Step-210 ledger records 180 reviewed/isolation inputs
and 751 UNKNOWNs. The final evidence join is a later derived artifact. It does
not overwrite that ledger or retrospectively claim that the earlier review
covered all 931 inputs. Historical counts and final proof classes answer
different questions.

Two approved behavior distinctions also remain explicit: empty Echo changes
from error to continuation; scope guidance has an approved wording suffix.
These are approved changes, not exact parity. Pre-existing demo/fixture problems
are tracked in CE issues [296](https://github.com/rapiddweller/datamimic/issues/296),
[297](https://github.com/rapiddweller/datamimic/issues/297),
[298](https://github.com/rapiddweller/datamimic/issues/298),
[299](https://github.com/rapiddweller/datamimic/issues/299),
[300](https://github.com/rapiddweller/datamimic/issues/300),
[301](https://github.com/rapiddweller/datamimic/issues/301),
[302](https://github.com/rapiddweller/datamimic/issues/302) and
[303](https://github.com/rapiddweller/datamimic/issues/303).
Matching a baseline failure does not fix it.

## What the evidence supports

**FACT:** the recorded final target passed its zero-violation completion policy;
all remaining UNKNOWNs were explicitly assessed; every inventoried input has a
named evidence class; invalid and superseded proof remains identifiable.

**INTERPRETATION:** explicit ownership, provenance checks and separate evidence
classes made this particular intervention reviewable. The observed import-finder
failure demonstrates why source identity needs module-level checks.

**UNKNOWN:** causal productivity gains; complete token or monetary cost; model
superiority; defect-detection recall; universal behavior equivalence; statistical
generalization to other projects. No adequate control group or complete
cost/time ledger is present in the analyzed packet.

The useful contribution is a traceable account of acceptance under uncertainty,
including a concrete false-provenance failure and its repair. The observed
result is narrower than “an autonomous refactor was proved correct.”

## Threats to validity

- **Construct validity:** declared rule satisfaction measures the chosen target,
  not total architectural quality. Input classification measures evidence
  coverage, not complete execution semantics. Tests and parser cases overlap.
- **Internal validity:** product changes, target amendments, checker releases,
  test-oracle changes and local service availability evolved together. The
  checker and product were co-developed. No causal attribution is justified.
- **External validity:** one CE repository, its particular descriptors, Python
  environment and service profiles. EE and other engines were not admitted.
- **Reliability:** hashes and raw events improve auditability; some historical
  temporary references may no longer exist. Reconstructible caches/source copies
  are identified separately. Private configurations need separate treatment.
- **Reviewer dependence:** agents share a model/provider ecosystem and the
  architect's goals. Separate agent reviews reduce one kind of implementation
  coupling; they do not establish unbiased external replication.
- **Selective reporting:** successful evidence must be read with retained VOID,
  failures, retries, skips, baseline debt and approved behavioral changes.

## Paper feasibility and next use

Recommended working title: **“Accepting an Agent-Assisted Refactoring Under
Explicit Architectural and Behavioral Uncertainty: A DATAMIMIC Case Study.”**

A paper can center on the three stated questions, report the evidence taxonomy,
explain the source-origin failure, and analyze how target/measurement changes
were kept distinct from implementation progress. Publication suitability and
novelty remain unassessed. A focused related-work review and human methods review
are required before presenting this as a submission-ready scientific paper.

The cheapest useful next steps are a human review of this report, claim-to-receipt
checks on a small sample, and a durable artifact deposit with an identifier.
A later controlled study would need fixed targets/tool profiles, baseline and
treatment conditions, a fixed test oracle, and recorded cost/time. It should be
a new prospective study, not an expensive retrospective rerun of all evidence.

The ACM policy distinguishes available artifacts, evaluated artifacts and
validated results. A ZIP committed to Git provides storage and a versioned
inventory; it does not itself establish those scientific evaluation outcomes.
[Artifact-policy reference](https://www.acm.org/publications/policies/artifact-review-and-badging-current).

## Evidence locators

The Git archive preserves experiment prose, Markdown and bounded receipts under
`repository/` and `local/`. Generated ArchKeel reports and the full source
snapshots remain in local archives by the architect's explicit instruction.
Raw-report access for a future paper therefore needs the separate Drive upload;
the Git ZIP alone is not the complete raw research artifact.
Start with these members:

- `local/ce-final-root-acceptance-20261012/evidence-index.json` and
  `astra-final-review.md`: final claims, artifact hashes and review limits.
- `local/ce-final-root-acceptance-20261012/join-summary.json` and
  `joined-runtime-evidence.jsonl`: 931-input evidence classes.
- `repository/docs/architecture/refactoring-study/experiment-2/completion-unknowns.json`:
  source-bound assessment of remaining UNKNOWNs.
- `local/ce-final-parity-ledger-20261012/`: corrected parser/negative/linter proof
  and invalidation records.
- `local/ce-final-local-parity-20261012/` and
  `local/ce-final-service-parity-20261012/`: local runtime and service receipts.
- `local/ce-step210-ledger.jsonl`: immutable historical input-review ledger.
- `repository/docs/architecture/refactoring-study/experiment-2/protocol.md`:
  frozen inputs, amendments and historical step notes, before archival editing.

LOCAL VERIFIED: archive member hashes, the 931-class arithmetic, 345 stored
hash references, 13 retained-target tests and a fresh architecture report
(488/488 files, 0 violations, 286 UNKNOWN records; unchanged Source/Target/analyzer
digests). Runtime results are retained acceptance
receipts, not rerun for this archival task. CI-ONLY VERIFICATION: the cited
exact-head jobs; no new CI outcome is claimed.
