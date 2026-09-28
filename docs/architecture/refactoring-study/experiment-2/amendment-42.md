# Amendment 42: sync marked architecture graphs

Sync both marked graphs with current ArchKeel validation evidence: remove the
stale `python_api → interfaces` edge and show the declared `randomness` edges
for Domains, IO and Runtime. No contract or code behavior changed.

LOCAL VERIFIED: candidate ArchKeel validation reports no `graph.drift`.
It still exits 2: nine unbaselined type-rule fingerprints, 84 `interface.unused`
diagnostics, and declared-rule status UNKNOWN. The empty baseline is unchanged.
Independent Luna and Terra review found no graph mismatch.

CI-ONLY VERIFICATION: no remote run.
