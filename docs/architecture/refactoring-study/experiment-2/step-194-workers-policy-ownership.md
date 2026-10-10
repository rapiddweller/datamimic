# Step 194 — keep worker execution and concurrency policy separate

Astra accepts `GENERATE-WORKERS` (three modules) and `GENERATE-POLICIES`
(one module) as two meaningful leaves at `a939a929`. The existing contract
already describes their responsibilities. No source or contract change is needed.

- Workers execute rows/pages, restore process-local state and return chunks.
- Policies inspect declared capabilities and explain reductions to one worker.
- Orchestration selects the backend, prepares inputs and consumes/finalizes results.
- Context owns copied state; IO owns clients, writes and exporter sessions.

Preserve policy precedence: MySQL sequence, unique/composite, domain identifiers,
delete, seeded. Their different traversal scopes are current behavior. Positional
sequence rejection remains an invalid-plan check, not a silent worker reduction.
The stdlib and explicit Ray entrypoints share one execution responsibility;
per-backend components or EE machinery would add no justified boundary.

The [receipt](step-194-workers-policy-ownership-receipt.json) binds the complete
caller/state/IO trace and independent static QA. Runtime proof remains separate
in [Step 193](step-193-real-workers.md).

A unique declaration beneath condition/if is a separate eligibility-scan
candidate. Static inspection alone establishes neither duplicate output nor a
broken supported contract. No CE issue or behavior change follows from that
suspicion without native evidence.

LOCAL VERIFIED: ownership trace and unchanged source/contract hashes.
CI-ONLY VERIFICATION: none for this static decision. Ray, exception transport,
nonempty serializer payloads and full behavioral parity remain open.
