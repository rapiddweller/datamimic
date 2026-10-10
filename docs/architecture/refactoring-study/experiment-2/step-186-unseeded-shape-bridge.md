# Step 186 — five unseeded shape comparisons

Fresh original `a219163e` and current `1244afff` captures pass the unchanged
strict comparator for five Step130 inputs: `unseeded_integer.xml`,
`unseeded_domain.xml`, `unseeded_entity.xml`, `unseeded_source.xml` and
`unseeded_datetime.xml`. All belong to `test_seeded_determinism`.

Ten exact native cases passed once, retaining two differing unseeded captures
each. Ten separate recorder calls used the same current observation schema.
Independent QA reconstructed all 30 typed captures and confirmed row counts,
field types and presence. All 20 negative controls reject missing evidence,
changed types or changed counts. Logs match with product/count, severity,
logger/task and order preserved; only measured runtime metadata varies.

The [receipt](step-186-unseeded-shape-bridge-receipt.json) pins the source,
inputs, shared dependency environment, raw rows/streams, observers and QA.
Both observers only read the captured values; the original recorder binds its
historical import. Three pre-test launch failures are retained, with zero
captures. No failed native assertion was retried. Native pytest's Faker
bootstrap warning is recorded; recorder streams have no WARN/ERROR.

These five fresh comparisons close the missing-shape evidence gap at these
endpoints. Frozen and Step130 old-recorder comparisons still **FAIL**; their
records are unchanged. The owner ledger stays **166 reviewed / 765 UNKNOWN**.
Empty export/nesting maps reflect these targetless, unnested cases. Full
descriptor coverage, historical-environment reproduction, transient effects,
public projections and EE remain unproved.

The targetless page's misleading export timing message also exists in the
original. Its source trace and acceptance example are recorded in existing
[CE #272](https://github.com/rapiddweller/datamimic/issues/272).

LOCAL VERIFIED: ten native cases, five strict comparisons, 20 negative
controls, independent raw-evidence QA, comparator self-test, Ruff and full
MyPy (488 files). Fresh ArchKeel 1.1.1 observes 488/488 files, 13 violations
and 254 canonical UNKNOWNs; `declared_rules` remains FAIL.
CI-ONLY VERIFICATION: at `1244afff`, 50 checks succeeded, four architecture
checks failed and four checks skipped. No CI claim for this later evidence
commit; full CE/EE acceptance remains open.
