# CE 5 plugin preparation review

Reviewed the diff from `8f89cd4dec9e29e8bb79f3bb0f4c96bae5ca404d` on
`feat/ce-5-agent-plugin`, including callers, tests, packaging and CI.

The MCP CLI validates an optional directory and passes it to the existing server
factory. Both transports retain the same authoring application and default root.
The shared skill preserves runtime discovery, transaction-owned proof, persisted
XML and the distinction between bounded capture and external delivery. Platform
guidance agrees with its current server instructions: observed ETags, Pending
polling and committing only the Ready execution identity. Plugin ZIP publication
is separate from Python distributions; package publishers select the Python artifact.

## Finding

The startup-dotenv integration test used a zero-argument `create_server` mock,
which rejects the newly passed keyword (`test_dotenv_entrypoints.py`,
`test_mcp_uses_startup_dotenv_and_process_environment_wins`). The parent reproduced
the two failing cases, aligned both factory mocks, then passed all 24 startup,
CLI and real stdio/SSE transport checks. Production behavior did not change.

## Architecture

Fresh full native collection: 534/534 files parsed, zero violations, 271 rules
PASS and 5 UNKNOWN. All 303 UNKNOWN records and all 20 validation diagnostics
match the prior independently assessed receipt exactly. Unresolved calls remain
1425 and typing positions 178. Contract and analyzer digests are unchanged.
[The receipt](completion-unknowns.json) binds the new source and validation digest;
its prior group assessments and approved limits are preserved. UNKNOWN remains
uncertainty, not proof of complete call resolution or public typing.

## Evidence boundary

Inspected local evidence under `/private/tmp/datamimic-ce5-20261019`: 2989 unit
tests passed, 15 skipped; project-venv Ruff and full MyPy passed (534 files).
Native installation/discovery is distinct from successful skill execution:
Claude failed with expired OAuth, and Codex rejected the configured model before
execution. Neither run proves selection, repair or complex-workflow behavior.
Inherited #333 weighted-variable CSV failure and #332 bounded-proof limitation
remain outside this plugin change; the triage evidence does not claim EE parity.

LOCAL VERIFIED: diff/caller review, fresh architecture identities and exact
retained UNKNOWN/diagnostic comparison; existing test logs inspected.
CI-ONLY VERIFICATION: exact candidate CI and platform matrix not run by this
reviewer. Native complex behavior and public installation remain unverified.
No merge or release approval is implied.
