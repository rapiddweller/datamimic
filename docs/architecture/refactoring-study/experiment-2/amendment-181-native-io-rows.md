# Amendment 181 — native IO rows and capture

2026-10-10. Decision: Astra, delegated architect. Base `0142679f`.

IO owns storage reads, source windows, database reads and capture collection;
Runtime owns their lifecycle and timing. Dataset/DSL columns and native cell
values are payload, while selectors, pagination and other controls stay typed.
Capture accepts native scalar rows; source and Memstore protocols require map
rows. Fixed row DTOs or JSON conversion would change these boundaries.

This new target decision supersedes Amendment 99's permission freeze only for
`TestResultExporter.get_result`, and Amendments 93/168's retained IO debt and
Amendment 176's depth hold only at the seven other positions below. Earlier
amendments did not grant these permissions. Amendments 179/180 keep their scope.

Append exactly two selectors per row to `IO-API-TYPES`, preserving all six
existing selectors. Prefix: `datamimic_ce.engine.io.api.`; field path: empty.
Both selectors use the complete annotation: one omits `container_depth` for
the single map occurrence; the other uses depth 2 for the native value.

| Qualified suffix | Position | Complete annotation |
| --- | --- | --- |
| `TestResultExporter.get_result` | return | `dict[str, list[object]]` |
| `MemstoreSource.get_all_data_by_type` | return | `list[dict[str, object]]` |
| `MemstoreSource.get_data_by_type` | return | `list[dict[str, object]]` |
| `read_generate_memstore_source` | return | `list[dict[str, object]]` |
| `ChunkSourceWindow.__init__` | pool | `list[dict[str, object]]` |
| `ChunkSourceWindow.read_page` | return | `list[dict[str, object]]` |
| `read_generate_database_source` | return | `list[dict[str, object]]` |
| `read_reference_rows` | return | `list[dict[str, object]]` |

These are explicit target widenings with accepted opacity, not proof of full
type closure or serializability. The concrete Memstore remains unannotated.
Capture returns its live dictionary; consume replaces product lists on append.
Memstore getters retain stored lists/rows; missing strict reads raise KeyError,
while full-pool reads return an empty list. Noncyclic selection copies the outer
list; cyclic selection deep-copies rows. Chunk pages are shallow slices; unique
selection retains its hashability constraints. Database reads pass results
through, except empty Mongo upsert yields `[{}]`. Reference reads build new maps
with native cells and reject either direction of row/target length mismatch.

Product envelopes with two maps, PreparedPage aliases, bare XML/file rows,
Iterables, nested-source objects, Properties and SQL remain separate open work.
No production, EE, ownership, dependency, baseline or oracle changes.

Expected delta: 53 → 37 findings, IO 31 → 15; preserve every remaining finding,
254 canonical / 200 measured UNKNOWNs and the 151-component/25-level structure.
Evidence: `/tmp/ce-resume-20261010/next-slice-166/`.

LOCAL VERIFIED: the exact contract guard fails against the old six selectors,
then passes unchanged in 170 boundary/source tests. Eight native-value and error
characterizations passed before the contract changed. A pre-existing import
ordering error in the touched source-routing test was then corrected; its 53
tests and Ruff for all three changed test files pass. Definition checks: 13 PASS;
package Ruff and full MyPy (488 files): PASS. Production source is unchanged.

Fresh ArchKeel 1.1.0 report: FAIL37, IO15, 200 measured UNKNOWNs, 488/488 files
parsed. Independent QA preserves all 37 remaining findings and 254 canonical
UNKNOWNs exactly, with unchanged source facts and 151 components / 25 levels.
Only finding aggregates and rule provenance change alongside the 16 new
allowance facts, eight with accepted opacity. Matcher checks pass 80 negative
cases and four broad-control checks in one source fixture.
Native amendment validation preserves the IO
widening but exits 2 with the same 19 usage-UNKNOWN diagnostics, 23 baseline-new
groups and no amendment artifact. Machine binding and full DSL/EE acceptance
remain open. CI-ONLY VERIFICATION: new-head checks pending.
