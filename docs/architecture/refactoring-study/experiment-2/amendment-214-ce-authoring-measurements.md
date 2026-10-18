# Amendment 214 — CE Authoring and Errors measurements

2026-10-18. Decision: parent and independent Astra review approved exact measured
ceilings after native validation reported zero violations and no baseline drift.
No source change, analyzer upgrade, general type permission or dependency edge.

| Measurement | Frozen actual | Previous ceiling | Current ceiling = actual |
|---|---:|---:|---:|
| Unresolved calls | 1246 | 1278 | 1395 |
| Typing signals | 147 | 143 | 174 |
| Cycle edges | 2 | 11 | 2 |
| Private crossings | 0 | 0 | 0 |
| Untyped private accesses | 0 | 3 | 0 |

The frozen typing observation already exceeded its ceiling by four. This was
not a green baseline. The current change adds 46 positions and removes 19,
net 27; no arbitrary four-position subset is inferred from the old ceiling.
All 174 current signals were reviewed: 165 object annotations, one literal-parser
Any, and eight unchanged exec/eval/getattr/cast signals. Their reasons are
untrusted-input validation, registry/schema scalar boundaries, internal passive
serialization/comparison, closed expression evaluation, passive decoding, and
preserved native literal behavior. Retained baseline signals remain visible.

Calls add 321 unresolved sites and remove 172. Current reason classes are
825 dynamic receivers, 520 dynamic expressions and 50 unproven lexical callable
bindings. New-site reasons are 217/84/20 respectively. These are native analysis
limits, not resolved calls. No source rewrite was made merely to alter counts.

## Exact evidence binding

Native tool: ArchKeel 2.0.0; Python 3.11.12. Both snapshots use analyzer digest
`7106e3595fa7df9269cb43ee280f9c557659db7bda171b1f65ff5619ab54aa24`.

Frozen source: clean `84a9f4657148bcfa0bc560908ed42b1d5fa3efab`, digest
`81f86023ad58442a08dd77cf72e9524a24c91b0466aa46645b732cc4f393d428`;
its original contract digest is
`289d6c0ee28d75e53e7ed8d057edbd66dd4004c5c362b6cccf5f7c095e0f7745`.
Candidate source: dirty adoption worktree at
`1d7060295501234af2d5ad1a5794c88e8a8ed160`, digest
`b71be23e55efeb0f42f13ee99877f8c0443d267c2ca09d6ce39356ec1c0a03e6`.
The measurement snapshot contract digest is
`1c33900d8fa88ce54aa686a1a86b95a597e028ed7c69a4d4457c7e1d0dd689d4`;
subsequent exact Protocol/ExporterError publications removed six violations
without changing these measurements. The final receipt binds the resulting target.

SHA256 of the complete current unresolved-call multiset:
`90a31f9f9050f27dd4fd855f1fde85c3583d501e86067475989c93b28a725950`.
Identity is sorted `(caller,path,expression,status,reason)`, preserving duplicates.
SHA256 of the complete current typing multiset:
`d554a100516234d7f50aea55d61f8319f6122dc3ff77bf85790a90fc8cce9275`.
Its frozen counterpart is
`919a7732fa6144c3c5591d89d2d6e964a8468e30ad48f3dad791860ddc1f2d45`.
Typing identity is sorted canonical JSON strings of `kind`, `subjects` and `data`,
excluding native FACT boundary-type allowances. Hashes use compact JSON UTF-8;
the explicit call line field is excluded, while native anonymous caller names retain
embedded locations. Six apparent call-site changes reflect those shifted names.
Typing comparison excludes evidence locations. Raw records and assessments remain in the
external adoption evidence, not copied into the maintained contract.

The ceilings have no headroom. UNKNOWN records stay UNKNOWN; this amendment does
not certify complete static typing, runtime coverage or delivery. Completion still
requires a fresh source/target/analyzer-bound native report and validation, plus
the independent assessment of every recorded UNKNOWN.
