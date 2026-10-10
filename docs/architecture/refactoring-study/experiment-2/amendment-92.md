# Amendment 92: empty echo diagnostics

2026-10-02. Decision: Astra, delegated architect. Base `008d4ce2`.

Align the relocated CE implementation with upstream
[PR284](https://github.com/rapiddweller/datamimic/pull/284), commit `b2899c2b`.
XML `<echo/>` and `<echo></echo>` produce a `None` text value. Diagnostic
output must not abort execution: emit the empty debug message `Echo - `
and continue. This intentionally changes the previous TypeError outcome;
it is not unchanged-behavior evidence for empty echoes.

Keep whitespace, quoting, interpolation and failed-placeholder warnings
unchanged. Type the statement value as `str | None` and execution as `None`.
No schema, contract allowance, baseline, budget, gate or existing XML changes.
Use temporary regression inputs; retain the 930-descriptor inventory.

EE still lacks the empty-value guard. This CE correction does not establish
EE behavior or physical parity. Full architecture/DSL acceptance remains open.
