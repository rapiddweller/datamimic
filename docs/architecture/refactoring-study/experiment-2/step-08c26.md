# Step 08C26: make service triage reproducible

`python3 -m script.architecture_study.service_inventory` prints a read-only
JSON inventory. It reuses the frozen oracle's tracked-XML classification and
adds declared client type/profile hints plus test-file basename mentions as
owner **candidates**, never as proven execution. It does not connect to a
service, resolve an endpoint, classify a setup as safe, or claim parity.

Current result: 273 service-classified descriptors. Owner candidates are
unresolved for 79, ambiguous for 44, and a single unproven mention for 150.
These are triage counts, not test-coverage counts. The outstanding parity
ledger remains 173, and this command alone cannot subtract those paths.

The initial draft emitted every XML client attribute, including a password in
an intentionally invalid fixture. The orchestrator caught this before commit.
The final command allow-lists only `id`, `system`, `environment`, `dbms`, and
`type` as `declared_hints`; no credential or resolved endpoint is emitted.
Independent review confirmed deterministic output, no service-call path, and
the redaction. The self-check exercises missing, ambiguous, misleading single
mention, and credential-filter cases. Ruff and `git diff --check` pass.

Next: manually resolve owner/setup/config for a small batch and record the
exact descriptor paths, container endpoint and destructive scope before
running them. Do not infer safety from this matrix.
