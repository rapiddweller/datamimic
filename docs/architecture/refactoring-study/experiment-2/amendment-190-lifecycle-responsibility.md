# Amendment 190 — CE lifecycle responsibility

Astra accepts the three-module `RUNTIME-LIFECYCLE` leaf at `72202ba0`.
It owns settings and session orchestration: parse, apply factory/transformer
policy, execute SetupTask and expose the existing captured results.

Correct the component responsibility and matching layout rationale to:

> Own run configuration and session orchestration, including descriptor parsing, setup execution and test-result capture.

Keep every package, public operation, dependency, module declaration and rule
predicate. No source or behavior changes. GenerateTask's outer-generation
`finally` owns chunk cleanup and conditional Ray shutdown; IO deletes chunks.
This clarification does not remove cleanup or move its lifetime. EE additionally
has session-final cleanup; CE does not gain EE infrastructure.

The receipt pins Astra's complete caller/state/IO trace. Static ownership
acceptance does not prove full lifecycle parity, failures or concurrency.
Native amendment binding remains a separate obligation; prose approval alone
does not satisfy it. Architecture findings remain open.

LOCAL VERIFIED: 13 definition checks pass; all 20 observed report sections
match the preceding report (13 violations, 254 canonical UNKNOWNs).
The native writer exits 2 with 19 usage-UNKNOWN diagnostics and writes no JSON
binding. CI-ONLY VERIFICATION: pending for this clarification.
