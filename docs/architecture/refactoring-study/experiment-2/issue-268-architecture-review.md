# Issue 268: bounded include review

Independent review of the working tree at `c84bf992e261ccd80e9491b95cf3f850013b3215`.
No source blocker remains in the reviewed subset. Architecture completion is
**not approved**: unresolved calls exceed the existing ceiling by six.

## Source and behavior

Literal setup-level XML dependencies are checked before root execution; native
parsing still owns property order and the entry descriptor directory. Each fresh
include receives the existing bounded transformation through a separate typed
hook, preserving the public root-only callback. Explicit separator setters carry
inherited values into source counting and smoke export. Public parsed `.tag`
access with a strict string guard removes the private `xml_tag` crossing.

The review reproduced and verified fixes for callback compatibility, inherited
CSV formatting, duplicate capture provenance and false memstore completeness.
A six-row cross-descriptor memstore previously produced a three-row capture
labelled complete; `UNRESOLVED_INCLUDES` now preserves UNKNOWN without claiming
local producers establish the whole source. Dynamic paths, generator-local
includes, cycles and duplicate/interpolated capture names remain unsupported.
Globally distinct names conservatively exclude some valid native nested models.
Build still rejects external XML includes; raw dry-run success is not Ready Build.

## Native measurement and decision

Final `architecture-current/architecture.json`: 534/534 files parsed, zero rule
violations, zero private crossings, two cycle edges and 178 typing positions.
The former `xml_tag` interface violation is absent. Contract and analyzer digests
match the CI baseline. The approved unresolved-call ceiling remains **1425**;
the current measurement is **1431**. Native validation exits 2 with this sole
failure: `measurement budget exceeded in calls_unresolved: 1425->1431`.
Baseline new/resolved violations are both zero; all 20 prior
`interface.usage_unknown` diagnostics are unchanged. Zero rule violations does
not pass the budget. Separate against-development validation is still pending.

Independent decoding of the CI ZIP and current native call records finds six new
unresolved sites after pairing line-shifted comprehensions and the changed
`SetupTask(...).execute` expression. No normalized unresolved site was removed.

| New site | Count | Native uncertainty |
|---|---:|---|
| `dryrun.py:272`, added `stmt.uri.endswith(".xml")` | 1 | dynamic attribute receiver |
| `dryrun.py:286`, `node.get("uri", "").endswith(...)` | 1 | dynamic expression |
| `dryrun.py:311`, `node.getparent()` | 1 | dynamic attribute receiver |
| `dryrun.py:321,323`, `uri.endswith(...)` | 2 | dynamic attribute receiver |
| `include_task.py:118`, `ctx.included_statement_transformer(statement)` | 1 | dynamic attribute receiver |

These are direct URI checks, native XML parent inspection and an explicitly typed,
None-guarded callback. Inspection supports keeping this simple implementation;
it does not convert the analyzer's six unresolved calls into resolved evidence.
An architect must decide whether to accept the exact 1425 -> 1431 budget change.
No cap, contract or completion receipt was changed by this review.

UNKNOWN records also rise **303 -> 310** (unknown positions 245 -> 252).
Ten added IDs and three removed IDs contain three unchanged `num_process`
positions with shifted occurrence identities. The genuine seven additions are
six getter/setter positions on `SetupStatement.default_separator` and
`default_line_separator` (`str | None` and `None`, inherited-surface binding
UNKNOWN), plus `SetupContext.__init__.included_statement_transformer`
(`StatementTransformer | None`, reason `other`). These annotations exist; their
effective binding remains unproven. No UNKNOWN classification is cleared.

## Evidence binding

Native source digest:
`001ada60a32d750fd73188e4d21c9a1dd07892e864e04ed18a172939cb54a480`.
SHA-256 of the canonical path/byte-hash manifest for all eight changed source files:
`eaeb366eda751e17055d0440db66687cbabcfe7839a559ee9e32dbb808f0ed1a`.
The source bytes were rechecked before writing this review.

Raw evidence is under `/private/tmp/datamimic-ce5-includes/`: native
`architecture-current/`, `independent-final-call-assessment.json`,
`independent-final-unknown-delta.json`, `reviewed-source-bytehashes.json` and the
early review/reproduction logs. Baseline: the prior closure `architecture-ci.zip`.

LOCAL VERIFIED: final narrow source review, independent native deltas and byte
binding; 17 corrected include tests and five callback integration tests passed.
Fresh Ruff/MyPy logs pass for all 534 files. Budget acceptance and final native
completion remain pending; the completion receipt is unchanged.
CI-ONLY VERIFICATION: current branch and native Windows not verified here.
No full Build graph support, merge or release approval is implied.
