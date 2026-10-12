# CE refactoring experiment — 12 October 2026

[Case-study report](report.md) · [Experiment documents and evidence](experiment-documents-and-evidence.zip)

The ZIP preserves **3,676 files** (21.7 MB):
525 original study/semantic-review documents, additional experiment prose,
final receipts, ledgers, scripts and bounded test evidence. `manifest.json`
records each original path, size and SHA-256. Failed, VOID and superseded evidence
is retained with its recorded status; historical ledgers are not promoted.

Source: `a219163e533d661bcc7bda0faa5ecc77909ab5aa`.
Delivered: `384b7723d950d8b312b1080d23ffd89a5343c9b0`.

## Verify and read

```sh
python3 verify_archive.py
```

The verifier checks the ZIP checksum, exact member set, payload sizes and hashes.
It rejects renderer output and embedded source/archive binaries. It does not
execute DATAMIMIC or establish scientific replication.

Unzip into an empty directory. `repository/` preserves original document paths;
`local/` preserves named evidence packets. Start with
`local/ce-final-root-acceptance-20261012/`. The supplied original handoff is under
`inputs/`. `analysis/separation-inventory.json` maps the separate local artifacts.

## Local artifacts

Generated ArchKeel HTML/JSON reports, report QA artifacts and source snapshots
are **local only**. They are excluded from this ZIP and from Git. The generated
semantic-review HTML is likewise local; its source review records stay available.
The local report archive preserves the original paths and every payload hash.

The local archives are under `test-artifacts/experiments/ce-refactoring-2026-10-12/`
in the main checkout. Alex owns their Drive upload; no upload is claimed here.
The Drive artifact must accompany a future paper. This Git ZIP alone is not the
complete raw research artifact. Private configurations remain separate and local.

Sixty live contract, test and study-script inputs stay readable outside the ZIP.
Other historical links point to their exact delivered Git revision. Extract both
document and local-report archives to restore the full original offline layout.
Caches and reproducible source copies are outside the archive scope; original
untracked `evidence/` and `.playwright-mcp/` are untouched.

LOCAL VERIFIED: all archive hashes, 345 stored hash references, 13 retained-target
tests and a fresh report: 488/488 files, 0 violations, 286 UNKNOWN records, unchanged
Source/Target/analyzer digests. CI-ONLY VERIFICATION: retained delivered-head runs
cited in the report; no new CI or runtime suite was run for archival.

Archival follow-up and the stale-test correction are recorded in
`analysis/archival-verification.md`; drafts under `analysis/drafts/` are superseded.
The full architecture suite now passes 1,680 tests, with 14 existing skips.
